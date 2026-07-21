from typing import Dict, List, Optional

from app.schemas import MealPlanRequest, UserProfile


def format_profile_context(profile: Optional[UserProfile]) -> str:
    """Converts optional profile fields into concise prompt context."""

    if profile is None:
        return "not provided"

    details = []
    if profile.fitness_goal:
        details.append(f"fitness goal: {profile.fitness_goal}")
    if profile.activity_level:
        details.append(f"activity level: {profile.activity_level}")
    if profile.height_cm:
        details.append(f"height: {profile.height_cm:g} cm")
    if profile.weight_kg:
        details.append(f"weight: {profile.weight_kg:g} kg")
    if profile.body_fat_percentage:
        details.append(f"body fat: {profile.body_fat_percentage:g}%")
    if profile.estimated_bmr:
        details.append(f"estimated BMR: {profile.estimated_bmr} kcal/day")
    if profile.dietary_preferences:
        details.append(f"dietary preferences: {', '.join(profile.dietary_preferences)}")
    if profile.foods_to_avoid:
        details.append(f"foods to avoid: {', '.join(profile.foods_to_avoid)}")

    return "; ".join(details) if details else "not provided"


def build_meal_llm_messages(request: MealPlanRequest) -> List[Dict[str, str]]:
    """Builds the messages used for the LLM meal planning spike."""

    available_seasonings = (
        ", ".join(request.available_seasonings)
        if request.available_seasonings
        else "not provided"
    )
    planning_notes = request.planning_notes or "none"
    profile_context = format_profile_context(request.profile)
    time_minutes = str(request.time_minutes) if request.time_minutes is not None else "not provided"

    system_prompt = (
        "You are LifeOS AI, a practical meal planning assistant. "
        "Create one meal recommendation using the user's ingredients first. "
        "Ingredient amounts may be exact (300g), approximate (half a head), or omitted. "
        "Use the amount when provided and make reasonable estimates when it is not. "
        "Treat the user's planning notes as goals and constraints. "
        "Do not assume every ingredient must be used; choose the best subset for the request. "
        "Only treat listed seasonings as already available. "
        "Do not recommend or require ingredients that are not listed. "
        "Return ingredients_to_use using the original ingredient strings exactly as provided, "
        "and do not include seasonings in that field. "
        "Keep the answer realistic, concise, and beginner-friendly. "
        "Return 4 to 6 concrete cooking steps as plain text strings without numbers, bullets, "
        "or labels such as 'Step 1'; the client will add the numbering. "
        "Include useful sequence, heat, time, and only the most relevant available seasonings. "
        "Return rough integer nutrition estimates for protein, "
        "calories, carbohydrates, and fat."
    )

    user_prompt = (
        f"Ingredients: {', '.join(request.ingredients)}\n"
        f"Planning notes: {planning_notes}\n"
        f"Long-term profile: {profile_context}\n"
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
    available_seasonings: Optional[List[str]] = None,
    profile: Optional[UserProfile] = None,
) -> str:
    """Builds the mock reasoning text for the meal plan response."""

    parts = [f"This mock plan uses ingredients you already have: {', '.join(ingredients_to_use)}."]

    if planning_notes:
        clean_notes = planning_notes.rstrip(".?!")
        parts.append(f"It considers your request: {clean_notes}.")

    profile_context = format_profile_context(profile)
    if profile_context != "not provided":
        parts.append(f"It also considers your profile: {profile_context}.")

    if time_minutes is not None:
        parts.append(f"It is designed to fit within about {time_minutes} minutes.")

    if available_seasonings:
        parts.append(f"It can use your saved seasonings: {', '.join(available_seasonings)}.")

    return " ".join(parts)
