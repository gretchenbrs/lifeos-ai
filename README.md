# LifeOS AI Backend

Minimal FastAPI backend for the LifeOS AI Lifestyle Decision Assistant.

## V1 Scope

- Backend API only
- No frontend
- No database
- No RAG
- No authentication
- Mock meal planning service instead of a real LLM

## Current Status

- `GET /health` is ready
- `POST /meal-plan` is ready
- `meal-plan` supports a small LLM spike through `mode=llm`
- Default behavior still uses mock logic so the backend remains easy to run locally

## Project Structure

```text
app/
  main.py
  schemas.py
  services/
    __init__.py
    meal_service.py
    llm_service.py
  prompts/
    __init__.py
    meal_prompts.py
requirements.txt
README.md
```

## Layer Responsibilities

- `app/main.py`: creates the FastAPI app and defines the API routes.
- `app/schemas.py`: stores the Pydantic request and response models.
- `app/services/meal_service.py`: chooses whether a request should use mock logic or the LLM spike.
- `app/services/llm_service.py`: contains the real OpenAI API call for the meal-planning spike.
- `app/prompts/meal_prompts.py`: contains both mock reasoning text helpers and the prompt-building logic for the LLM path.

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

## LLM Spike Setup

To test the real LLM path, set your OpenAI API key before starting the server:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

Optional: choose a model explicitly.

```bash
export OPENAI_MODEL="gpt-5.5"
```

If you do not set `OPENAI_API_KEY`, the API still works in mock mode.

## Endpoints

### `GET /health`

Returns a simple service status response:

```json
{
  "status": "ok"
}
```

### `POST /meal-plan`

By default this endpoint uses mock logic:

```bash
curl -X POST "http://127.0.0.1:8000/meal-plan" \
  -H "Content-Type: application/json" \
  -d '{
    "ingredients": ["chicken breast", "rice", "broccoli"],
    "goal": "high protein dinner",
    "time_minutes": 25,
    "dietary_preferences": ["gluten free"]
  }'
```

To test the LLM spike, call the same endpoint with `mode=llm`:

```bash
curl -X POST "http://127.0.0.1:8000/meal-plan?mode=llm" \
  -H "Content-Type: application/json" \
  -d '{
    "ingredients": ["chicken breast", "rice", "broccoli"],
    "goal": "high protein dinner",
    "time_minutes": 25,
    "dietary_preferences": ["gluten free"]
  }'
```

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
- The mock path still exists so you can keep building even without an API key.
- The LLM spike is intentionally small: one endpoint, one prompt builder, and one OpenAI service.
- Splitting out a prompt layer makes it easier to evolve from mock text to real prompt engineering without rewriting the route layer.
