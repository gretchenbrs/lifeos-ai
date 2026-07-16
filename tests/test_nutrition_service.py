import unittest
from unittest.mock import patch

from app.services.nutrition_service import USDANutritionService


class USDANutritionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = USDANutritionService()

    def test_generic_beef_uses_a_stable_canonical_reference(self) -> None:
        food = self.service.canonical_foods["beef"]

        self.assertEqual(food["fdcId"], 169430)
        self.assertIn("Beef, carcass", food["description"])

    def test_search_nutrients_support_usda_search_response_shape(self) -> None:
        food = {
            "foodNutrients": [
                {"nutrientName": "Protein", "unitName": "G", "value": 19.0},
                {"nutrientName": "Energy", "unitName": "KCAL", "value": 100.0},
            ]
        }

        nutrients = self.service._extract_nutrients(food)

        self.assertEqual(nutrients, {"protein": 19.0, "calories": 100.0})

    def test_kilojoules_are_not_treated_as_calories(self) -> None:
        food = {
            "foodNutrients": [
                {"nutrientName": "Protein", "unitName": "G", "value": 19.0},
                {"nutrientName": "Energy", "unitName": "KJ", "value": 900.0},
            ]
        }

        nutrients = self.service._extract_nutrients(food)

        self.assertEqual(nutrients, {"protein": 19.0})

    def test_multiple_ingredients_keep_search_fallback_and_canonical_foods(self) -> None:
        tuna_search_food = {
            "fdcId": 334194,
            "description": "Fish, tuna, light, canned in water, drained solids",
            "foodNutrients": [
                {"nutrientName": "Protein", "unitName": "G", "value": 19.4},
                {"nutrientName": "Energy", "unitName": "KCAL", "value": 90.0},
            ],
        }
        beef_food = self.service.canonical_foods["beef"]
        lettuce_food = {
            "fdcId": 169247,
            "description": "Lettuce, cos or romaine, raw",
        }

        with (
            patch.dict("os.environ", {"USDA_API_KEY": "test-key"}),
            patch.object(
                self.service,
                "_find_best_food",
                side_effect=[tuna_search_food, beef_food, lettuce_food],
            ),
            patch.object(
                self.service,
                "_get_nutrients",
                side_effect=[
                    None,
                    {"protein": 17.32, "calories": 291.0},
                    {"protein": 1.0, "calories": 17.0},
                ],
            ),
        ):
            estimate = self.service.estimate(
                ["tuna (200g)", "beef (400g)", "lettuce (100g)"]
            )

        self.assertIsNotNone(estimate)
        assert estimate is not None
        self.assertEqual(estimate.protein_grams, 109)
        self.assertEqual(estimate.calories, 1361)
        self.assertIn("tuna (200g", estimate.coverage)
        self.assertIn("beef (400g", estimate.coverage)
        self.assertIn("lettuce (100g", estimate.coverage)


if __name__ == "__main__":
    unittest.main()
