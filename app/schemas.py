from typing import List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class MealPlanRequest(BaseModel):
    ingredients: List[str] = Field(
        ...,
        min_length=1,
        description="Ingredients the user already has at home.",
    )
    goal: str = Field(..., min_length=1, description="The user's meal goal.")
    time_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        le=240,
        description="Optional time budget for the meal.",
    )
    dietary_preferences: List[str] = Field(
        default_factory=list,
        description="Optional dietary preferences such as vegetarian or high-protein.",
    )


class MealPlanResponse(BaseModel):
    meal_name: str
    reasoning: str
    ingredients_to_use: List[str]
    missing_items: List[str]
    estimated_protein: int
    estimated_calories: int
