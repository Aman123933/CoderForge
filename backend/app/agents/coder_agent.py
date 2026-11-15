from typing import Any, Dict
from backend.app.agents.base_agent import BaseAgent


class CoderAgent(BaseAgent):
    """
    Generates code for EXACTLY ONE FILE based on a structured file specification.
    """

    def __init__(self, llm):
        super().__init__(
            llm,
            agent_name="CoderAgent",
            require_json=False,  # code is NOT JSON
        )

    def generate_code(self, file_spec: Dict[str, Any]) -> str:
        self._validate_file_spec(file_spec)

        prompt = self._build_prompt(file_spec)
        code = self.call_llm(prompt)

        return code.strip()

    def _validate_file_spec(self, file_spec: Dict[str, Any]) -> None:
        required_keys = {"file_path", "file_purpose", "requirements"}
        missing = required_keys - file_spec.keys()

        if missing:
            raise ValueError(f"Missing keys in file_spec: {missing}")

        if not isinstance(file_spec["requirements"], list):
            raise ValueError("requirements must be a list")

    def _build_prompt(self, file_spec: Dict[str, Any]) -> str:
        requirements_text = "\n".join(
            f"- {req}" for req in file_spec["requirements"]
        )

        return f"""
You are a CODER AGENT acting as a senior software engineer.

⚠️ STRICT RULES ⚠️
- Generate code for EXACTLY ONE FILE.
- Do NOT create folders.
- Do NOT reference files that are not mentioned.
- Do NOT explain anything.
- Do NOT use markdown.
- Output ONLY valid code.

FILE PATH:
{file_spec["file_path"]}

FILE PURPOSE:
{file_spec["file_purpose"]}

REQUIREMENTS:
{requirements_text}
"""



    def _call_llm(self, prompt: str) -> str:
        try:
            if hasattr(self.llm_client, "generate"):
                return self.llm_client.generate(prompt)
            else:
                raise ValueError("Unsupported LLM client interface")
        except Exception as e:
            self.logger.error(f"Code generation failed: {e}")
            raise


