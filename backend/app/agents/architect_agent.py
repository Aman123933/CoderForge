import json
from typing import Dict, Any
from backend.app.agents.base_agent import BaseAgent


class ArchitectAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__(llm, agent_name="ArchitectAgent")

    def design_architecture(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_prompt(plan_data)
        response = self.call_llm(prompt)
        data = self.parse_json(response)

        self.validate_required_keys(
            data,
            {
                "system_overview",
                "backend_components",
                "frontend_components",
                "data_models",
                "integration_points",
                "external_dependencies",
            },
        )

        return data

    def _build_prompt(self, plan_data: Dict[str, Any]) -> str:
        return f"""
You are an ARCHITECT AGENT in a multi-agent coding system.

⚠️ EXECUTION IS STRICTLY FORBIDDEN ⚠️
- Do NOT write code
- Do NOT create files
- Do NOT generate folder structures
- Do NOT mention frameworks, libraries, or tools
- Do NOT explain anything

OUTPUT (STRICT JSON ONLY):
{{
  "system_overview": "",
  "backend_components": [],
  "frontend_components": [],
  "data_models": [],
  "integration_points": [],
  "external_dependencies": []
}}

RULES:
- Conceptual only
- No implementation details
- No technology names
- Minimal and scalable

PLAN DATA:
{json.dumps(plan_data, indent=2)}
"""


    def _parse_and_validate(self, response_text: str) -> Dict[str, Any]:
        if response_text.strip().startswith("```"):
            raise ValueError("ArchitectAgent returned markdown instead of raw JSON")

        data = json.loads(response_text)

        required_keys = {
            "system_overview",
            "backend_components",
            "frontend_components",
            "data_models",
            "integration_points",
            "external_dependencies"
        }

        missing = required_keys - data.keys()
        if missing:
            raise ValueError(f"ArchitectAgent missing keys: {missing}")

        return data
