from fastapi import FastAPI

from app.schemas import HealthResponse, MealPlanRequest, MealPlanResponse
from app.services import MealPlanningService


app = FastAPI(
    title="LifeOS AI Backend",
    description="Minimal backend API for the LifeOS AI lifestyle assistant.",
    version="0.1.0",
)

meal_planning_service = MealPlanningService()


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/meal-plan", response_model=MealPlanResponse)
def create_meal_plan(request: MealPlanRequest) -> MealPlanResponse:
    return meal_planning_service.create_meal_plan(request)
