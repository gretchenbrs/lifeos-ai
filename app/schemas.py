from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class MealPlanRequest(BaseModel):
    ingredients: list[str] = Field(
        ...,
        min_length=1,
        description="Ingredients the user already has at home.",
    )
    goal: str = Field(..., min_length=1, description="The user's meal goal.")
    time_minutes: int | None = Field(
        default=None,
        ge=1,
        le=240,
        description="Optional time budget for the meal.",
    )
    dietary_preferences: list[str] = Field(
        default_factory=list,
        description="Optional dietary preferences such as vegetarian or high-protein.",
    )


class MealPlanResponse(BaseModel):
    meal_name: str
    reasoning: str
    ingredients_to_use: list[str]
    missing_items: list[str]
    estimated_protein: int
    estimated_calories: int
