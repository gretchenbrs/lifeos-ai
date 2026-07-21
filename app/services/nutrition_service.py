"""Small USDA FoodData Central integration for exact gram-based estimates."""

import json
import os
from dataclasses import dataclass
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.services.quantity_parser import QuantityParser


FDC_BASE_URL = "https://api.nal.usda.gov/fdc/v1"


@dataclass
class NutritionEstimate:
    protein_grams: int
    calories: int
    carbs_grams: int
    fat_grams: int
    coverage: str


class USDANutritionService:
    """Looks up basic food data and calculates totals for exact gram quantities."""

    # Broad user terms need a stable source record instead of whichever search item
    # happens to rank first. The selected description is returned in the coverage note.
    canonical_foods = {
        "chicken": {
            "fdcId": 171447,
            "description": "Chicken, broilers or fryers, meat and skin, raw",
        },
        "beef": {
            "fdcId": 169430,
            "description": "Beef, carcass, separable lean and fat, choice, raw",
        },
        "egg": {
            "fdcId": 171287,
            "description": "Egg, whole, raw, fresh",
        },
        "rice": {
            "fdcId": 168878,
            "description": "Rice, white, long-grain, regular, enriched, cooked",
        },
    }

    undesirable_description_terms = (
        "lunchmeat",
        "deli",
        "breaded",
        "roll,",
        "sliced",
        "seasoned",
        "prepackaged",
    )

    ambiguous_piece_foods = {"chicken", "beef"}
    preferred_portion_modifiers = {"egg": "large"}
    canonical_food_aliases = {"eggs": "egg"}

    def __init__(self) -> None:
        self.quantity_parser = QuantityParser()

    def estimate(self, ingredients: list[str]) -> Optional[NutritionEstimate]:
        """Returns USDA totals for gram amounts or supported count-based amounts."""

        api_key = os.getenv("USDA_API_KEY")
        if not api_key:
            return None

        protein_total = 0.0
        calorie_total = 0.0
        carbohydrate_total = 0.0
        fat_total = 0.0
        covered_items: list[str] = []
        omitted_items: list[str] = []

        for ingredient in ingredients:
            parsed_ingredient = self.quantity_parser.parse_ingredient(ingredient)
            if parsed_ingredient is None:
                omitted_items.append(f"{ingredient} (amount was not recognized)")
                continue

            food_name = parsed_ingredient.name
            amount = parsed_ingredient.quantity
            unit = parsed_ingredient.unit
            if unit not in {"gram", "piece"}:
                omitted_items.append(f"{ingredient} (unit is not supported for USDA totals)")
                continue

            food = self._find_best_food(food_name, api_key)
            if food is None:
                omitted_items.append(f"{ingredient} (no USDA match found)")
                continue

            # A count of a broad food such as "chicken" does not identify a
            # consistent piece size. Keep the source mapping stable, but do not
            # invent a gram weight for that amount.
            canonical_name = self._canonical_food_name(food_name)
            if unit == "piece" and canonical_name in self.ambiguous_piece_foods:
                omitted_items.append(f"{ingredient} (food is too broad for a piece estimate)")
                continue

            nutrients = self._get_nutrients(food["fdcId"], api_key, canonical_name)
            if not self._has_core_nutrients(nutrients):
                # Some USDA search records cannot be retrieved from the detail
                # endpoint, even though the search response includes nutrients.
                nutrients = self._extract_nutrients(food)
            if nutrients is None:
                omitted_items.append(f"{ingredient} (USDA nutrients were unavailable)")
                continue

            protein_per_100g = nutrients.get("protein")
            calories_per_100g = nutrients.get("calories")
            if protein_per_100g is None or calories_per_100g is None:
                omitted_items.append(f"{ingredient} (USDA nutrients were incomplete)")
                continue

            if unit == "piece":
                reference_portion_grams = nutrients.get("reference_portion_grams")
                if reference_portion_grams is None:
                    omitted_items.append(f"{ingredient} (no USDA reference portion was available)")
                    continue
                grams = amount * reference_portion_grams
                piece_label = "piece" if amount == 1 else "pieces"
                coverage_item = (
                    f"{food_name} ({amount:g} {piece_label}, using a USDA reference serving "
                    f"of {reference_portion_grams:g}g each; USDA match: "
                    f"{food['description']})"
                )
            else:
                grams = parsed_ingredient.grams
                if grams is None:
                    omitted_items.append(f"{ingredient} (could not convert amount to grams)")
                    continue
                coverage_item = (
                    f"{food_name} ({grams:g}g; USDA match: {food['description']})"
                )

            multiplier = grams / 100
            protein_total += protein_per_100g * multiplier
            calorie_total += calories_per_100g * multiplier
            carbohydrate_total += nutrients.get("carbohydrates", 0) * multiplier
            fat_total += nutrients.get("fat", 0) * multiplier
            covered_items.append(coverage_item)

        if not covered_items:
            return None

        coverage = (
            "Calculated from USDA FoodData Central for: "
            + ", ".join(covered_items)
            + ". Piece-based amounts are approximate; other informal amounts are not included."
        )
        if omitted_items:
            coverage += " Not included: " + ", ".join(omitted_items) + "."
        return NutritionEstimate(
            protein_grams=round(protein_total),
            calories=round(calorie_total),
            carbs_grams=round(carbohydrate_total),
            fat_grams=round(fat_total),
            coverage=coverage,
        )

    def _find_best_food(self, food_name: str, api_key: str) -> Optional[dict[str, Any]]:
        canonical_food = self.canonical_foods.get(self._canonical_food_name(food_name))
        if canonical_food is not None:
            return canonical_food

        payload = {
            "query": food_name,
            "dataType": ["Foundation", "SR Legacy"],
            "pageSize": 10,
        }
        response = self._request_json(
            f"{FDC_BASE_URL}/foods/search?api_key={quote(api_key)}",
            method="POST",
            payload=payload,
        )
        foods = response.get("foods", []) if response else []
        candidates = [food for food in foods if food.get("fdcId")]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda food: (self._score_food(food, food_name), -int(food["fdcId"])),
        )

    def _canonical_food_name(self, food_name: str) -> str:
        normalized_name = food_name.strip().lower()
        return self.canonical_food_aliases.get(normalized_name, normalized_name)

    def _score_food(self, food: dict[str, Any], query: str) -> int:
        """Favor plain, raw Foundation or SR Legacy foods over processed variants."""

        description = food.get("description", "").lower()
        query_terms = [term for term in query.lower().split() if len(term) > 2]
        score = 0

        if food.get("dataType") == "Foundation":
            score += 5
        if "raw" in description:
            score += 4
        score += sum(3 for term in query_terms if term in description)
        score -= sum(8 for term in self.undesirable_description_terms if term in description)
        return score

    def _get_nutrients(
        self,
        fdc_id: int,
        api_key: str,
        food_name: str,
    ) -> Optional[dict[str, float]]:
        response = self._request_json(
            f"{FDC_BASE_URL}/food/{fdc_id}?api_key={quote(api_key)}",
            method="GET",
        )
        if response is None:
            return None

        nutrients = self._extract_nutrients(response)

        portions = response.get("foodPortions", [])
        preferred_modifier = self.preferred_portion_modifiers.get(food_name.lower())
        if preferred_modifier:
            portions = sorted(
                portions,
                key=lambda portion: portion.get("modifier", "").lower()
                != preferred_modifier,
            )

        for portion in portions:
            gram_weight = portion.get("gramWeight")
            if gram_weight:
                nutrients["reference_portion_grams"] = float(gram_weight)
                break

        return nutrients

    def _extract_nutrients(self, food: dict[str, Any]) -> dict[str, float]:
        """Reads the nutrient shapes returned by either USDA endpoint."""

        nutrients: dict[str, float] = {}
        for item in food.get("foodNutrients", []):
            nutrient = item.get("nutrient", {})
            name = nutrient.get("name") or item.get("nutrientName", "")
            amount = item.get("amount", item.get("value"))
            if amount is None:
                continue

            unit_name = nutrient.get("unitName") or item.get("unitName", "")

            if name == "Protein":
                nutrients["protein"] = float(amount)
            elif name == "Carbohydrate, by difference":
                nutrients["carbohydrates"] = float(amount)
            elif name == "Total lipid (fat)":
                nutrients["fat"] = float(amount)
            elif (
                name in {"Energy", "Energy (Atwater General Factors)"}
                and unit_name.lower() == "kcal"
            ):
                nutrients["calories"] = float(amount)

        return nutrients

    def _has_core_nutrients(self, nutrients: Optional[dict[str, float]]) -> bool:
        return bool(
            nutrients
            and nutrients.get("protein") is not None
            and nutrients.get("calories") is not None
        )

    def _request_json(
        self,
        url: str,
        method: str,
        payload: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            url,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"} if data else {},
        )
        try:
            with urlopen(request, timeout=8) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return None
