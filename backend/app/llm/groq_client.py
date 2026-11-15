import os
from groq import Groq
from backend.app.llm.llm_interface import LLMInterface


class GroqClient(LLMInterface):
    def __init__(self, api_key: str | None = None, model: str = "llama3-70b-8192"):
        api_key = api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set")

        self.client = Groq(api_key=api_key)
        self.model = model

    def generate(self, prompt: str) -> str:
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return completion.choices[0].message.content.strip()
