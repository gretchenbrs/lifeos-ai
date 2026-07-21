"""Normalizes common ingredient amount formats before nutrition lookup."""

import re
from dataclasses import dataclass
from typing import Optional


INGREDIENT_AMOUNT_PATTERN = re.compile(
    r"^\s*(?P<name>.+?)\s*\(\s*(?P<amount>[^()]+)\s*\)\s*$"
)
NUMBER_UNIT_PATTERN = re.compile(
    r"^\s*(?P<quantity>\d+(?:\.\d+)?)\s*(?P<unit>[a-zA-Z]+)\s*$"
)
NUMBER_PATTERN = re.compile(r"^\s*(?P<quantity>\d+(?:\.\d+)?)\s*$")


@dataclass(frozen=True)
class ParsedIngredientAmount:
    name: str
    quantity: float
    unit: str
    grams: Optional[float]


class QuantityParser:
    """Converts clear user-entered amounts into a small set of standard units."""

    unit_aliases = {
        "g": "gram",
        "gram": "gram",
        "grams": "gram",
        "kg": "kilogram",
        "kgs": "kilogram",
        "kilogram": "kilogram",
        "kilograms": "kilogram",
        "oz": "ounce",
        "ounce": "ounce",
        "ounces": "ounce",
        "lb": "pound",
        "lbs": "pound",
        "pound": "pound",
        "pounds": "pound",
        "pc": "piece",
        "pcs": "piece",
        "piece": "piece",
        "pieces": "piece",
        "pic": "piece",
        "pics": "piece",
        "egg": "piece",
        "eggs": "piece",
        "ml": "milliliter",
        "milliliter": "milliliter",
        "milliliters": "milliliter",
        "l": "liter",
        "liter": "liter",
        "liters": "liter",
        "cup": "cup",
        "cups": "cup",
        "tbsp": "tablespoon",
        "tablespoon": "tablespoon",
        "tablespoons": "tablespoon",
        "tsp": "teaspoon",
        "teaspoon": "teaspoon",
        "teaspoons": "teaspoon",
        "slice": "slice",
        "slices": "slice",
        "can": "can",
        "cans": "can",
        "package": "package",
        "packages": "package",
    }

    gram_multipliers = {
        "gram": 1,
        "kilogram": 1000,
        "ounce": 28.3495,
        "pound": 453.592,
    }

    natural_count_foods = {"egg", "eggs"}

    def parse_ingredient(self, ingredient: str) -> Optional[ParsedIngredientAmount]:
        """Parses strings such as ``egg (1 pc)`` without guessing ambiguous units."""

        ingredient_match = INGREDIENT_AMOUNT_PATTERN.match(ingredient)
        if ingredient_match is None:
            return None

        name = ingredient_match.group("name").strip()
        raw_amount = ingredient_match.group("amount")
        amount_match = NUMBER_UNIT_PATTERN.match(raw_amount)
        if not name:
            return None

        if amount_match is None:
            bare_number_match = NUMBER_PATTERN.match(raw_amount)
            if name.lower() not in self.natural_count_foods or bare_number_match is None:
                return None
            return ParsedIngredientAmount(
                name=name,
                quantity=float(bare_number_match.group("quantity")),
                unit="piece",
                grams=None,
            )

        quantity = float(amount_match.group("quantity"))
        raw_unit = amount_match.group("unit").lower()
        unit = self.unit_aliases.get(raw_unit)
        if quantity <= 0 or unit is None:
            return None

        multiplier = self.gram_multipliers.get(unit)
        grams = quantity * multiplier if multiplier is not None else None
        if multiplier is not None:
            unit = "gram"
        return ParsedIngredientAmount(
            name=name,
            quantity=quantity,
            unit=unit,
            grams=grams,
        )
