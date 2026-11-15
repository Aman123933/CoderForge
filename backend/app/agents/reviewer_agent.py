import json
from typing import Dict, Any
from backend.app.agents.base_agent import BaseAgent


class ReviewerAgent(BaseAgent):
    """
    Reviews generated code and returns structured feedback.
    NEVER modifies or executes code.
    """

    def __init__(self, llm):
        super().__init__(llm, agent_name="ReviewerAgent")

    def review_code(
        self,
        code: str,
        architecture_context: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        prompt = self._build_prompt(code, architecture_context)
        response = self.call_llm(prompt)
        data = self.parse_json(response)

        self.validate_required_keys(
            data,
            {"summary", "issues", "recommendations"},
        )

        if not isinstance(data["issues"], list):
            raise ValueError("ReviewerAgent 'issues' must be a list")

        for issue in data["issues"]:
            if not isinstance(issue, dict):
                raise ValueError("Each issue must be an object")
            for key in {"severity", "description", "location"}:
                if key not in issue:
                    raise ValueError(f"Issue missing key: {key}")

        return data

    def _build_prompt(
        self,
        code: str,
        architecture_context: Dict[str, Any] | None
    ) -> str:
        context_block = ""
        if architecture_context:
            context_block = f"""
---------------------------------
ARCHITECTURE CONTEXT
---------------------------------
{json.dumps(architecture_context, indent=2)}
"""

        return f"""
You are a REVIEWER AGENT in a multi-agent autonomous coding system.

⚠️ EXECUTION IS STRICTLY FORBIDDEN ⚠️
- Do NOT write code
- Do NOT modify code
- Do NOT refactor code
- Do NOT execute anything
- Do NOT create files
- Do NOT suggest libraries or frameworks
- Do NOT act autonomously

Your ONLY responsibility is to REVIEW the provided CODE
and return STRUCTURED FEEDBACK.

---------------------------------
INPUT CODE (READ-ONLY)
---------------------------------
{code}

{context_block}

---------------------------------
OUTPUT (STRICT JSON ONLY)
---------------------------------
{{
  "summary": "",
  "issues": [
    {{
      "severity": "critical | major | minor",
      "description": "",
      "location": ""
    }}
  ],
  "recommendations": []
}}

---------------------------------
REVIEW RULES
---------------------------------
- Focus on correctness, clarity, maintainability, and safety
- Do NOT rewrite code
- Do NOT suggest specific tools or frameworks
- Be concise and actionable
"""


    def _parse_and_validate(self, response_text: str) -> Dict[str, Any]:
        if response_text.strip().startswith("```"):
            raise ValueError("ReviewerAgent returned markdown instead of raw JSON")

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError("ReviewerAgent output is not valid JSON") from e

        required_keys = {"summary", "issues", "recommendations"}
        missing = required_keys - data.keys()
        if missing:
            raise ValueError(f"ReviewerAgent missing keys: {missing}")

        if not isinstance(data["issues"], list):
            raise ValueError("ReviewerAgent 'issues' must be a list")

        for issue in data["issues"]:
            if not isinstance(issue, dict):
                raise ValueError("Each issue must be an object")
            for key in {"severity", "description", "location"}:
                if key not in issue:
                    raise ValueError(f"Issue missing key: {key}")

        return data
