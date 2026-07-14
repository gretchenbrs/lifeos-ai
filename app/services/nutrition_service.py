"""Small USDA FoodData Central integration for exact gram-based estimates."""

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


FDC_BASE_URL = "https://api.nal.usda.gov/fdc/v1"
GRAM_INGREDIENT_PATTERN = re.compile(
    r"^\s*(?P<name>.+?)\s*\(\s*(?P<grams>\d+(?:\.\d+)?)\s*g\s*\)\s*$",
    re.IGNORECASE,
)
PIECE_INGREDIENT_PATTERN = re.compile(
    r"^\s*(?P<name>.+?)\s*\(\s*(?P<count>\d+(?:\.\d+)?)\s*"
    r"(?:piece|pieces|pc|pcs|pic|pics)\s*\)\s*$",
    re.IGNORECASE,
)


@dataclass
class NutritionEstimate:
    protein_grams: int
    calories: int
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

    def estimate(self, ingredients: list[str]) -> Optional[NutritionEstimate]:
        """Returns USDA totals for gram amounts or supported count-based amounts."""

        api_key = os.getenv("USDA_API_KEY")
        if not api_key:
            return None

        protein_total = 0.0
        calorie_total = 0.0
        covered_items: list[str] = []

        for ingredient in ingredients:
            parsed_ingredient = self._parse_gram_ingredient(ingredient)
            if parsed_ingredient is None:
                continue

            food_name, amount, unit = parsed_ingredient
            food = self._find_best_food(food_name, api_key)
            if food is None:
                continue

            # A count of a broad food such as "chicken" does not identify a
            # consistent piece size. Keep the source mapping stable, but do not
            # invent a gram weight for that amount.
            if unit == "piece" and food_name.strip().lower() in self.canonical_foods:
                continue

            nutrients = self._get_nutrients(food["fdcId"], api_key)
            if nutrients is None:
                continue

            protein_per_100g = nutrients.get("protein")
            calories_per_100g = nutrients.get("calories")
            if protein_per_100g is None or calories_per_100g is None:
                continue

            grams = amount
            coverage_item = (
                f"{food_name} ({amount:g}g; USDA match: {food['description']})"
            )
            if unit == "piece":
                reference_portion_grams = nutrients.get("reference_portion_grams")
                if reference_portion_grams is None:
                    continue
                grams = amount * reference_portion_grams
                coverage_item = (
                    f"{food_name} ({amount:g} pieces, using a USDA reference serving "
                    f"of {reference_portion_grams:g}g each; USDA match: "
                    f"{food['description']})"
                )

            multiplier = grams / 100
            protein_total += protein_per_100g * multiplier
            calorie_total += calories_per_100g * multiplier
            covered_items.append(coverage_item)

        if not covered_items:
            return None

        coverage = (
            "Calculated from USDA FoodData Central for: "
            + ", ".join(covered_items)
            + ". Piece-based amounts are approximate; other informal amounts are not included."
        )
        return NutritionEstimate(
            protein_grams=round(protein_total),
            calories=round(calorie_total),
            coverage=coverage,
        )

    def _parse_gram_ingredient(self, ingredient: str) -> Optional[tuple[str, float, str]]:
        match = GRAM_INGREDIENT_PATTERN.match(ingredient)
        if match is not None:
            name = match.group("name").strip()
            grams = float(match.group("grams"))
            if name and grams > 0:
                return name, grams, "gram"

        match = PIECE_INGREDIENT_PATTERN.match(ingredient)
        if match is None:
            return None

        name = match.group("name").strip()
        count = float(match.group("count"))
        if not name or count <= 0:
            return None
        return name, count, "piece"

    def _find_best_food(self, food_name: str, api_key: str) -> Optional[dict[str, Any]]:
        canonical_food = self.canonical_foods.get(food_name.strip().lower())
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

    def _get_nutrients(self, fdc_id: int, api_key: str) -> Optional[dict[str, float]]:
        response = self._request_json(
            f"{FDC_BASE_URL}/food/{fdc_id}?api_key={quote(api_key)}",
            method="GET",
        )
        if response is None:
            return None

        nutrients: dict[str, float] = {}
        for item in response.get("foodNutrients", []):
            nutrient = item.get("nutrient", {})
            name = nutrient.get("name") or item.get("nutrientName", "")
            amount = item.get("amount")
            if amount is None:
                continue

            if name == "Protein":
                nutrients["protein"] = float(amount)
            elif (
                name in {"Energy", "Energy (Atwater General Factors)"}
                and nutrient.get("unitName") == "kcal"
            ):
                nutrients["calories"] = float(amount)

        for portion in response.get("foodPortions", []):
            gram_weight = portion.get("gramWeight")
            if gram_weight:
                nutrients["reference_portion_grams"] = float(gram_weight)
                break

        return nutrients

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
