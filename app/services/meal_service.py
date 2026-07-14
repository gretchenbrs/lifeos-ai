from typing import Dict, List

from app.prompts.meal_prompts import build_meal_reasoning
from app.schemas import MealPlanRequest, MealPlanResponse
from app.services.llm_service import LLMMealPlanningService
from app.services.nutrition_service import USDANutritionService


class MealPlanningService:
    """Switches between mock and LLM meal planning implementations."""

    def __init__(self) -> None:
        self.mock_service = MockMealPlanningService()
        self.llm_service = LLMMealPlanningService()
        self.nutrition_service = USDANutritionService()

    def create_meal_plan(
        self,
        request: MealPlanRequest,
        mode: str = "mock",
    ) -> MealPlanResponse:
        if mode == "llm":
            meal_plan = self.llm_service.create_meal_plan(request)
        else:
            meal_plan = self.mock_service.create_meal_plan(request)

        nutrition_estimate = self.nutrition_service.estimate(request.ingredients)
        if nutrition_estimate is not None:
            meal_plan.estimated_protein = nutrition_estimate.protein_grams
            meal_plan.estimated_calories = nutrition_estimate.calories
            meal_plan.nutrition_source = "USDA FoodData Central"
            meal_plan.nutrition_coverage = nutrition_estimate.coverage

        return meal_plan


class MockMealPlanningService:
    """Simple mock service that returns a meal plan without calling an LLM."""

    protein_keywords = (
        "chicken",
        "turkey",
        "beef",
        "salmon",
        "tuna",
        "shrimp",
        "tofu",
        "tempeh",
        "egg",
        "greek yogurt",
        "beans",
        "lentils",
    )

    protein_estimates: Dict[str, int] = {
        "chicken": 31,
        "turkey": 29,
        "beef": 26,
        "salmon": 25,
        "tuna": 24,
        "tofu": 12,
        "eggs": 12,
        "egg": 6,
        "greek yogurt": 17,
        "beans": 9,
        "lentils": 9,
        "rice": 4,
        "pasta": 5,
        "quinoa": 8,
    }

    calorie_estimates: Dict[str, int] = {
        "chicken": 165,
        "turkey": 170,
        "beef": 250,
        "salmon": 208,
        "tuna": 132,
        "tofu": 120,
        "eggs": 140,
        "egg": 70,
        "greek yogurt": 100,
        "beans": 120,
        "lentils": 116,
        "rice": 205,
        "pasta": 200,
        "quinoa": 222,
        "broccoli": 55,
        "spinach": 23,
        "bell pepper": 24,
        "tomato": 22,
        "avocado": 160,
    }

    def create_meal_plan(self, request: MealPlanRequest) -> MealPlanResponse:
        normalized_ingredients = [ingredient.strip() for ingredient in request.ingredients]
        lower_ingredients = [ingredient.lower() for ingredient in normalized_ingredients]
        planning_context = request.planning_notes
        if request.profile and request.profile.fitness_goal:
            planning_context = f"{planning_context} {request.profile.fitness_goal}"

        ingredients_to_use = self._select_ingredients(
            normalized_ingredients,
            lower_ingredients,
            planning_context,
        )
        lower_selected_ingredients = [ingredient.lower() for ingredient in ingredients_to_use]
        meal_name = self._build_meal_name(lower_selected_ingredients)
        lower_seasonings = [item.lower() for item in request.available_seasonings]
        missing_items = self._suggest_missing_items(
            lower_ingredients + lower_seasonings,
            planning_context,
        )

        estimated_protein = self._estimate_total(
            lower_selected_ingredients,
            self.protein_estimates,
        )
        estimated_calories = self._estimate_total(
            lower_selected_ingredients,
            self.calorie_estimates,
        )

        if estimated_protein == 0:
            estimated_protein = 18
        if estimated_calories == 0:
            estimated_calories = 450

        reasoning = build_meal_reasoning(
            planning_notes=request.planning_notes,
            time_minutes=request.time_minutes,
            ingredients_to_use=ingredients_to_use,
            missing_items=missing_items,
            available_seasonings=request.available_seasonings,
            profile=request.profile,
        )

        return MealPlanResponse(
            meal_name=meal_name,
            reasoning=reasoning,
            ingredients_to_use=ingredients_to_use,
            missing_items=missing_items,
            estimated_protein=estimated_protein,
            estimated_calories=estimated_calories,
        )

    def _build_meal_name(self, ingredients: List[str]) -> str:
        if any("chicken" in ingredient for ingredient in ingredients):
            return "Chicken Nourish Bowl"
        if any("salmon" in ingredient or "tuna" in ingredient for ingredient in ingredients):
            return "Protein-Packed Fish Plate"
        if any(
            "tofu" in ingredient or "lentil" in ingredient or "bean" in ingredient
            for ingredient in ingredients
        ):
            return "Plant Protein Power Bowl"
        if any("egg" in ingredient for ingredient in ingredients):
            return "Quick Savory Egg Skillet"
        return "Balanced Pantry Bowl"

    def _select_ingredients(
        self,
        ingredients: List[str],
        lower_ingredients: List[str],
        planning_notes: str,
    ) -> List[str]:
        """Prioritize protein ingredients when the user's request calls for it."""

        if not self._needs_high_protein(planning_notes):
            return ingredients[:5]

        protein_indexes = [
            index
            for index, ingredient in enumerate(lower_ingredients)
            if any(keyword in ingredient for keyword in self.protein_keywords)
        ]
        other_indexes = [
            index for index in range(len(ingredients)) if index not in protein_indexes
        ]
        selected_indexes = (protein_indexes + other_indexes)[:5]
        return [ingredients[index] for index in selected_indexes]

    def _suggest_missing_items(
        self,
        ingredients: List[str],
        planning_notes: str,
    ) -> List[str]:
        suggestions = []

        needs_high_protein = self._needs_high_protein(planning_notes)
        has_protein = any(
            keyword in ingredient
            for ingredient in ingredients
            for keyword in self.protein_keywords
        )
        if needs_high_protein and not has_protein:
            suggestions.append("protein source such as chicken, tofu, eggs, or beans")

        if not any("garlic" in ingredient or "onion" in ingredient for ingredient in ingredients):
            suggestions.append("garlic or onion")
        if not any("olive oil" in ingredient or "oil" in ingredient for ingredient in ingredients):
            suggestions.append("olive oil")
        if not any(
            "salt" in ingredient
            or "pepper" in ingredient
            or "seasoning" in ingredient
            for ingredient in ingredients
        ):
            suggestions.append("basic seasoning")

        return suggestions

    def _needs_high_protein(self, planning_notes: str) -> bool:
        context = planning_notes.lower()
        return "high protein" in context or "muscle gain" in context

    def _estimate_total(self, ingredients: List[str], lookup: Dict[str, int]) -> int:
        total = 0
        for ingredient in ingredients:
            for keyword, value in lookup.items():
                if keyword in ingredient:
                    total += value
                    break
        return total
