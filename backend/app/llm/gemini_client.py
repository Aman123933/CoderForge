import os
import google.generativeai as genai
from backend.app.llm.llm_interface import LLMInterface


class GeminiClient(LLMInterface):
    def __init__(self, api_key: str | None = None, model: str = "gemini-1.5-flash"):
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def generate(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text.strip()
