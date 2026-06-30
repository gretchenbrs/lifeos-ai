def build_meal_reasoning(
    goal: str,
    time_minutes: int | None,
    dietary_preferences: list[str],
    ingredients_to_use: list[str],
    missing_items: list[str],
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
