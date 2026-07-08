from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.config import load_local_env
from app.schemas import HealthResponse, MealPlanRequest, MealPlanResponse
from app.services import MealPlanningService


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

load_local_env()


app = FastAPI(
    title="LifeOS AI Backend",
    description="Minimal backend API for the LifeOS AI lifestyle assistant.",
    version="0.1.0",
)

meal_planning_service = MealPlanningService()


@app.get("/", include_in_schema=False)
def home_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/meal-plan", response_model=MealPlanResponse)
def create_meal_plan(
    request: MealPlanRequest,
    mode: Literal["mock", "llm"] = "mock",
) -> MealPlanResponse:
    try:
        return meal_planning_service.create_meal_plan(request, mode=mode)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
