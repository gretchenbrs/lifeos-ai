# LifeOS AI Backend

Minimal FastAPI backend plus a lightweight built-in frontend demo for the LifeOS AI Lifestyle Decision Assistant.

LifeOS AI is an AI lifestyle decision assistant focused on helping users make better everyday choices around meals first, with future expansion into grocery planning, travel, and other personalized planning workflows.

## V1 Scope

- Backend API
- Lightweight built-in frontend demo
- No database
- No RAG
- No authentication
- Mock meal planning service instead of a real LLM

## Current Status

- `GET /health` is ready
- `POST /meal-plan` is ready
- `meal-plan` supports a small LLM spike through `mode=llm`
- Exact gram amounts can use USDA FoodData Central for protein and calorie totals
- `/` serves a simple frontend demo page for testing the planner
- Default behavior still uses mock logic so the backend remains easy to run locally

## Why This Project

This project is not meant to be a thin chat wrapper. The goal is to build a modular AI decision backend that can gradually grow into a more personalized lifestyle platform with structured user context, memory, and additional planning domains.

## Next Steps

- make the meal planner more reliable with better prompts and error handling
- improve the built-in frontend demo UX
- add a second planning capability after the meal flow feels solid

## Project Structure

```text
app/
  main.py
  schemas.py
  static/
    index.html
    preferences.html
  services/
    __init__.py
    meal_service.py
    llm_service.py
    nutrition_service.py
  prompts/
    __init__.py
    meal_prompts.py
requirements.txt
README.md
```

## Layer Responsibilities

- `app/main.py`: creates the FastAPI app and defines the API routes.
- `app/schemas.py`: stores the Pydantic request and response models.
- `app/static/index.html`: provides a lightweight demo frontend that calls the backend directly.
- `app/static/preferences.html`: stores baseline fitness and food preferences in the browser.
- `app/services/meal_service.py`: chooses whether a request should use mock logic or the LLM spike.
- `app/services/llm_service.py`: contains the real OpenAI API call for the meal-planning spike.
- `app/services/nutrition_service.py`: uses USDA FoodData Central for nutrition totals when an ingredient has an exact gram amount.
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

3. Create a local `.env` file:

```bash
cp .env.example .env
```

Then open `.env` and add your real OpenAI key.

For factual nutrition estimates, also add a USDA FoodData Central key:

```bash
USDA_API_KEY="your_usda_api_key_here"
```

4. Run the API locally:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

Open these pages after the server starts:

- `http://127.0.0.1:8000/` for the frontend demo
- `http://127.0.0.1:8000/preferences` for baseline fitness and food preferences
- `http://127.0.0.1:8000/docs` for Swagger docs

## LLM Spike Setup

The app automatically loads `.env` from the project root if it exists.

Recommended `.env` values:

```bash
OPENAI_API_KEY="your_api_key_here"
```

Optional: choose a model explicitly.

```bash
OPENAI_MODEL="gpt-5.5"
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
    "planning_notes": "High-protein dinner, gluten free, low oil.",
    "time_minutes": 25
  }'
```

To test the LLM spike, call the same endpoint with `mode=llm`:

```bash
curl -X POST "http://127.0.0.1:8000/meal-plan?mode=llm" \
  -H "Content-Type: application/json" \
  -d '{
    "ingredients": ["chicken breast", "rice", "broccoli"],
    "planning_notes": "High-protein dinner, gluten free, low oil.",
    "time_minutes": 25
  }'
```

Example request:

```json
{
  "ingredients": ["chicken breast (300g)", "rice (1 bowl)", "broccoli"],
  "planning_notes": "High-protein dinner, gluten free, low oil, avoid frying.",
  "time_minutes": 25,
  "available_seasonings": ["salt", "black pepper", "soy sauce"]
}
```

## Frontend Demo

The built-in frontend at `/` lets you:

- search a starter catalog or enter any ingredient
- add exact or informal amounts such as `300g`, `2 pieces`, or `a handful` after adding an ingredient
- describe goals, dietary needs, and cooking preferences in one free-text field
- manage usual seasonings in a separate pantry dialog saved in the browser
- save long-term fitness and food preferences on a separate profile page
- save optional body metrics and view a client-side estimated BMR for planning context
- switch between `mock` and `llm` modes
- submit a request without writing cURL
- view the structured meal response in a simple UI

When a user enters an ingredient with an exact gram amount, such as `chicken breast (300g)`, the backend calculates protein and calories from USDA FoodData Central. Supported count-based amounts, such as `chicken thigh (2 pieces)` or `chicken thigh (4 pic)`, use a USDA reference serving and are marked as approximate. Other informal or missing amounts remain outside that calculation, so the response includes a coverage note.

Example response:

```json
{
  "meal_name": "Chicken Nourish Bowl",
  "reasoning": "This mock plan uses ingredients you already have: chicken breast, rice, broccoli. It considers your request: High-protein dinner, gluten free, low oil. It is designed to fit within about 25 minutes. You could improve flavor or flexibility with: garlic or onion, olive oil, basic seasoning.",
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
- The profile-page BMR value is an estimate for planning context, not a medical measurement or a daily calorie target.
