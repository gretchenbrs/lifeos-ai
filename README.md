# LifeOS AI Backend

Minimal FastAPI backend for the LifeOS AI Lifestyle Decision Assistant.

## V1 Scope

- Backend API only
- No frontend
- No database
- No RAG
- No authentication
- Mock meal planning service instead of a real LLM

## Project Structure

```text
app/
  main.py
  schemas.py
  services/
    __init__.py
    meal_service.py
  prompts/
    __init__.py
    meal_prompts.py
requirements.txt
README.md
```

## Layer Responsibilities

- `app/main.py`: creates the FastAPI app and defines the API routes.
- `app/schemas.py`: stores the Pydantic request and response models.
- `app/services/meal_service.py`: contains the meal-planning business logic and builds the response data.
- `app/prompts/meal_prompts.py`: contains prompt-style text building logic used for mock reasoning today and real LLM prompts later.

## Setup

1. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the API locally:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Endpoints

### `GET /health`

Returns a simple service status response:

```json
{
  "status": "ok"
}
```

### `POST /meal-plan`

Example request:

```json
{
  "ingredients": ["chicken breast", "rice", "broccoli"],
  "goal": "high protein dinner",
  "time_minutes": 25,
  "dietary_preferences": ["gluten free"]
}
```

Example response:

```json
{
  "meal_name": "Chicken Nourish Bowl",
  "reasoning": "This mock plan focuses on your goal of high protein dinner and uses ingredients you already have: chicken breast, rice, broccoli. It is designed to fit within about 25 minutes. It also considers these dietary preferences: gluten free. You could improve flavor or flexibility with: garlic or onion, olive oil, basic seasoning.",
  "ingredients_to_use": ["chicken breast", "rice", "broccoli"],
  "missing_items": ["garlic or onion", "olive oil", "basic seasoning"],
  "estimated_protein": 35,
  "estimated_calories": 425
}
```

## Notes

- `/docs` provides the automatic Swagger UI from FastAPI.
- The meal planning logic is intentionally simple so it can later be replaced with a real AI service.
- Splitting out a prompt layer now makes it easier to swap mock reasoning text for real LLM prompts without rewriting the service layer.
