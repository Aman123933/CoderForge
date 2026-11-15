import json
from typing import Dict, Any
from backend.app.agents.base_agent import BaseAgent


PLANNER_PROMPT_TEMPLATE = """
You are a PLANNER AGENT in a multi-agent coding system.

⚠️ EXECUTION IS STRICTLY FORBIDDEN ⚠️
- Do NOT write code
- Do NOT create files
- Do NOT generate folder structures
- Do NOT explain anything
- Do NOT act autonomously

Your ONLY job is to convert the given INTENT DATA
into an ordered list of HIGH-LEVEL development steps.

---------------------------------
OUTPUT (STRICT JSON ONLY)
---------------------------------
{
  "project_name": "<short_snake_case_name>",
  "steps": []
}

---------------------------------
RULES
---------------------------------
1. Steps must be HIGH LEVEL (architecture, APIs, UI)
2. No implementation details
3. No frameworks mentioned
4. Steps must be logically ordered
5. Output ONLY valid JSON
"""


class PlannerAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__(llm, agent_name="PlannerAgent")

    def create_plan(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (
            PLANNER_PROMPT_TEMPLATE
            + "\n"
            + json.dumps(intent_data, indent=2)
        )

        response = self.call_llm(prompt)
        plan = self.parse_json(response)

        self.validate_required_keys(plan, {"project_name", "steps"})

        if not isinstance(plan["steps"], list):
            raise ValueError("PlannerAgent 'steps' must be a list")

        return plan
