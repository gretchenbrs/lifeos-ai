from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class UserProfile(BaseModel):
    """Long-term preferences reused across meal-planning requests."""

    fitness_goal: Optional[str] = Field(
        default=None,
        description="A long-term goal such as fat loss, muscle gain, or maintenance.",
    )
    activity_level: Optional[str] = Field(
        default=None,
        description="The user's typical training or activity level.",
    )
    age: Optional[int] = Field(default=None, ge=13, le=120)
    sex_for_bmr: Optional[Literal["female", "male"]] = Field(
        default=None,
        description="Optional setting used only for the Mifflin-St Jeor BMR estimate.",
    )
    height_cm: Optional[float] = Field(default=None, ge=80, le=250)
    weight_kg: Optional[float] = Field(default=None, ge=20, le=400)
    body_fat_percentage: Optional[float] = Field(default=None, ge=1, le=80)
    estimated_bmr: Optional[int] = Field(
        default=None,
        ge=500,
        le=5000,
        description="A client-side Mifflin-St Jeor estimate in kcal per day.",
    )
    dietary_preferences: List[str] = Field(
        default_factory=list,
        description="Long-term dietary preferences or restrictions.",
    )
    foods_to_avoid: List[str] = Field(
        default_factory=list,
        description="Foods the user usually prefers not to eat.",
    )


class MealPlanRequest(BaseModel):
    ingredients: List[str] = Field(
        ...,
        min_length=1,
        description="Ingredients the user already has at home.",
    )
    planning_notes: str = Field(
        default="",
        description="Optional free-text goal, dietary needs, and cooking preferences.",
    )
    time_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        le=240,
        description="Optional time budget for the meal.",
    )
    available_seasonings: List[str] = Field(
        default_factory=list,
        description="Seasonings the user keeps at home.",
    )
    profile: Optional[UserProfile] = Field(
        default=None,
        description="Optional long-term preferences saved by the user.",
    )


class MealPlanResponse(BaseModel):
    meal_name: str
    reasoning: str
    ingredients_to_use: List[str]
    missing_items: List[str]
    estimated_protein: int
    estimated_calories: int
    nutrition_source: str = "Mock estimate"
    nutrition_coverage: str = (
        "Estimated from ingredient names because USDA nutrition needs exact grams or a "
        "specific countable food such as chicken thigh."
    )
