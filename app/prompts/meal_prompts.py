from typing import Dict, List, Optional

from app.schemas import MealPlanRequest


def build_meal_llm_messages(request: MealPlanRequest) -> List[Dict[str, str]]:
    """Builds the messages used for the LLM meal planning spike."""

    dietary_preferences = (
        ", ".join(request.dietary_preferences)
        if request.dietary_preferences
        else "none"
    )
    time_minutes = str(request.time_minutes) if request.time_minutes is not None else "not provided"

    system_prompt = (
        "You are LifeOS AI, a practical meal planning assistant. "
        "Create one meal recommendation using the user's ingredients first. "
        "Keep the answer realistic, concise, and beginner-friendly. "
        "Return estimated_protein and estimated_calories as rough integer estimates. "
        "Only include missing_items that are actually helpful."
    )

    user_prompt = (
        f"Ingredients: {', '.join(request.ingredients)}\n"
        f"Goal: {request.goal}\n"
        f"Time limit in minutes: {time_minutes}\n"
        f"Dietary preferences: {dietary_preferences}"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_meal_reasoning(
    goal: str,
    time_minutes: Optional[int],
    dietary_preferences: List[str],
    ingredients_to_use: List[str],
    missing_items: List[str],
) -> str:
    """Builds the mock reasoning text for the meal plan response."""

    parts = [
        f"This mock plan focuses on your goal of {goal.lower()}",
        f"and uses ingredients you already have: {', '.join(ingredients_to_use)}.",
    ]

    if time_minutes is not None:
        parts.append(f"It is designed to fit within about {time_minutes} minutes.")

    if dietary_preferences:
        parts.append(
            f"It also considers these dietary preferences: {', '.join(dietary_preferences)}."
        )

    if missing_items:
        parts.append(
            f"You could improve flavor or flexibility with: {', '.join(missing_items)}."
        )

    return " ".join(parts)
