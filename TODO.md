# LifeOS AI TODO

## Nutrition Data Integration

- Add a nutrition service backed by USDA FoodData Central.
- Keep the USDA API key in the backend environment only.
- Match user ingredients to canonical food records before calculating nutrition.
- Calculate calories, protein, carbohydrates, and fat from user-provided amounts.
- Keep LLM responsibilities limited to understanding requests, choosing meals, and explaining results.
- Replace mock nutrition estimates only after the ingredient matching flow is reliable.

## Pantry Experience

- Start with a curated local seasoning catalog and autocomplete.
- Allow custom seasonings when the catalog has no match.
- Move pantry data from browser storage to a user profile after authentication and a database exist.
