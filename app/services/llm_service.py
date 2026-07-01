import os
from typing import Optional

from app.prompts.meal_prompts import build_meal_llm_messages
from app.schemas import MealPlanRequest, MealPlanResponse


class LLMMealPlanningService:
    """OpenAI-backed meal planning service used for the LLM spike."""

    def __init__(self) -> None:
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.5")

    def create_meal_plan(self, request: MealPlanRequest) -> MealPlanResponse:
        api_key = os.getenv("OPENAI_API_KEY")
        self._validate_api_key(api_key)

        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError(
                "The openai package is not installed. Run 'pip install -r requirements.txt' first."
            ) from error

        client = OpenAI(api_key=api_key)
        response = client.responses.parse(
            model=self.model,
            input=build_meal_llm_messages(request),
            text_format=MealPlanResponse,
        )

        parsed_response = response.output_parsed
        if parsed_response is None:
            raise RuntimeError("The model response could not be parsed into the meal plan schema.")

        return parsed_response

    def _validate_api_key(self, api_key: Optional[str]) -> None:
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Add it to your environment before using mode=llm."
            )

        normalized_key = api_key.strip()
        if not normalized_key:
            raise RuntimeError(
                "OPENAI_API_KEY is empty. Set it to a real OpenAI API key before using mode=llm."
            )

        if "你的key" in normalized_key or "your_key" in normalized_key.lower():
            raise RuntimeError(
                "OPENAI_API_KEY still looks like a placeholder. Replace it with a real OpenAI API key."
            )

        try:
            normalized_key.encode("ascii")
        except UnicodeEncodeError as error:
            raise RuntimeError(
                "OPENAI_API_KEY contains non-ASCII characters. Make sure you pasted the real key value."
            ) from error
