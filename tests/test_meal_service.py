import unittest

from app.schemas import MealPlanRequest
from app.services.llm_service import LLMMealPlanningService
from app.services.meal_service import MealPlanningService, MockMealPlanningService


class MockMealPlanningServiceTests(unittest.TestCase):
    def test_plan_uses_only_available_ingredients_and_returns_steps(self) -> None:
        request = MealPlanRequest(
            ingredients=["tuna (200g)", "rice (300g)", "lettuce (100g)"],
            available_seasonings=["soy sauce"],
            planning_notes="low oil",
        )

        plan = MockMealPlanningService().create_meal_plan(request)

        self.assertEqual(plan.ingredients_to_use, request.ingredients)
        self.assertEqual(len(plan.steps), 4)
        self.assertIn("soy sauce", plan.steps[2])
        self.assertGreaterEqual(plan.estimated_protein, 0)
        self.assertGreaterEqual(plan.estimated_calories, 0)
        self.assertGreaterEqual(plan.estimated_carbs, 0)
        self.assertGreaterEqual(plan.estimated_fat, 0)


class MealPlanningServiceTests(unittest.TestCase):
    def test_removes_model_step_numbers_before_returning_response(self) -> None:
        steps = LLMMealPlanningService._normalize_steps(
            ["1. Soak the noodles.", "Step 2: Stir-fry the tofu.", "3) Serve warm."]
        )

        self.assertEqual(
            steps,
            ["Soak the noodles.", "Stir-fry the tofu.", "Serve warm."],
        )

    def test_restores_original_amounts_after_llm_rewrites_ingredients(self) -> None:
        service = MealPlanningService()

        nutrition_ingredients = service._nutrition_ingredients(
            ["salmon (150g)", "rice (150g)", "lettuce (20g)", "spinach (30g)"],
            [
                "salmon 150g",
                "rice 150g, assumed cooked",
                "lettuce 20g",
                "spinach 30g",
                "soy sauce",
            ],
        )

        self.assertEqual(
            nutrition_ingredients,
            ["salmon (150g)", "rice (150g)", "lettuce (20g)", "spinach (30g)"],
        )


if __name__ == "__main__":
    unittest.main()
