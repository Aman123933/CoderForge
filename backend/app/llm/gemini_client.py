import os
from typing import Optional, Dict, Any
from backend.app.llm.llm_interface import LLMInterface


class GeminiClient(LLMInterface):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.temperature = temperature
        self._model = None
        self.call_count = 0
        self.last_usage: Dict[str, int] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }
        self.cumulative_usage: Dict[str, int] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }

    def _ensure_model(self):
        if self._model is None:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY not set")
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(
                self.model_name,
                generation_config={"temperature": self.temperature},
            )
        return self._model

    def generate(self, prompt: str) -> str:
        model = self._ensure_model()
        self.call_count += 1
        response = model.generate_content(prompt)

        # Extract usage metadata
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0

        usage = getattr(response, "usage_metadata", None)
        if usage:
            input_tokens = getattr(usage, "prompt_token_count", 0) or 0
            output_tokens = getattr(usage, "candidates_token_count", 0) or 0
            total_tokens = getattr(usage, "total_token_count", 0) or (input_tokens + output_tokens)

        self.last_usage = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        }
        self.cumulative_usage["input_tokens"] += input_tokens
        self.cumulative_usage["output_tokens"] += output_tokens
        self.cumulative_usage["total_tokens"] += total_tokens

        return response.text.strip()

    def get_usage(self) -> Dict[str, Any]:
        return {
            "llm_calls": self.call_count,
            "last_usage": dict(self.last_usage),
            "cumulative_usage": dict(self.cumulative_usage),
        }

    def reset_usage(self) -> None:
        self.call_count = 0
        self.last_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        self.cumulative_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

