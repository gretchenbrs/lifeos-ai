from typing import Dict, List, Optional

from app.schemas import MealPlanRequest


def build_meal_llm_messages(request: MealPlanRequest) -> List[Dict[str, str]]:
    """Builds the messages used for the LLM meal planning spike."""

    available_seasonings = (
        ", ".join(request.available_seasonings)
        if request.available_seasonings
        else "not provided"
    )
    planning_notes = request.planning_notes or "none"
    time_minutes = str(request.time_minutes) if request.time_minutes is not None else "not provided"

    system_prompt = (
        "You are LifeOS AI, a practical meal planning assistant. "
        "Create one meal recommendation using the user's ingredients first. "
        "Ingredient amounts may be exact (300g), approximate (half a head), or omitted. "
        "Use the amount when provided and make reasonable estimates when it is not. "
        "Treat the user's planning notes as goals and constraints. "
        "Do not assume every ingredient must be used; choose the best subset for the request. "
        "Only treat listed seasonings as already available. "
        "Keep the answer realistic, concise, and beginner-friendly. "
        "Return estimated_protein and estimated_calories as rough integer estimates. "
        "Only include missing_items that are actually helpful."
    )

    user_prompt = (
        f"Ingredients: {', '.join(request.ingredients)}\n"
        f"Planning notes: {planning_notes}\n"
        f"Time limit in minutes: {time_minutes}\n"
        f"Available seasonings: {available_seasonings}"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_meal_reasoning(
    planning_notes: str,
    time_minutes: Optional[int],
    ingredients_to_use: List[str],
    missing_items: List[str],
    available_seasonings: Optional[List[str]] = None,
) -> str:
    """Builds the mock reasoning text for the meal plan response."""

    parts = [f"This mock plan uses ingredients you already have: {', '.join(ingredients_to_use)}."]

    if planning_notes:
        clean_notes = planning_notes.rstrip(".?!")
        parts.append(f"It considers your request: {clean_notes}.")

    if time_minutes is not None:
        parts.append(f"It is designed to fit within about {time_minutes} minutes.")

    if available_seasonings:
        parts.append(f"It can use your saved seasonings: {', '.join(available_seasonings)}.")

    if missing_items:
        parts.append(
            f"You could improve flavor or flexibility with: {', '.join(missing_items)}."
        )

    return " ".join(parts)
