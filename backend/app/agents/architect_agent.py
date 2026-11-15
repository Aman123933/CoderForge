import json
from typing import Dict, Any, List
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

        if "files" not in data or not isinstance(data.get("files"), list) or len(data["files"]) == 0:
            data["files"] = self._derive_files(data)
        else:
            # Validate each file spec in files
            validated_files = []
            for item in data["files"]:
                if isinstance(item, dict) and "file_path" in item:
                    item.setdefault("file_purpose", f"Module for {item.get('file_path')}")
                    if "requirements" not in item or not isinstance(item["requirements"], list):
                        item["requirements"] = ["Implement required functionality"]
                    validated_files.append(item)
            data["files"] = validated_files if validated_files else self._derive_files(data)

        return data

    def _derive_files(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        files = [
            {
                "file_path": "main.py",
                "file_purpose": "Application entry point and core logic",
                "requirements": [
                    "Implement application initialization and primary endpoints/functions",
                    "Handle input/output properly and expose runnable interface",
                ],
            }
        ]
        backend_components = data.get("backend_components", [])
        for comp in backend_components:
            name = comp.replace(" ", "_").lower() if isinstance(comp, str) else "module"
            clean_name = "".join(c for c in name if c.isalnum() or c == "_")
            if clean_name and clean_name != "main":
                files.append({
                    "file_path": f"{clean_name}.py",
                    "file_purpose": f"Component implementation for {comp}",
                    "requirements": [f"Implement functionality for {comp}"],
                })
        return files

    def _build_prompt(self, plan_data: Dict[str, Any]) -> str:
        return f"""
You are an ARCHITECT AGENT in a multi-agent coding system.

⚠️ EXECUTION IS STRICTLY FORBIDDEN ⚠️
- Do NOT write full code implementation
- Do NOT create physical files on the filesystem
- Do NOT explain anything outside JSON

OUTPUT (STRICT JSON ONLY):
{{
  "system_overview": "",
  "backend_components": [],
  "frontend_components": [],
  "data_models": [],
  "integration_points": [],
  "external_dependencies": [],
  "files": [
    {{
      "file_path": "main.py",
      "file_purpose": "Entry point and primary application setup",
      "requirements": ["Initialize application", "Implement core handlers"]
    }}
  ]
}}

RULES:
- Provide an explicit list of 1 to 3 modular 'files' needed to implement the solution (e.g. main.py, models.py)
- Always include an entrypoint file (main.py) containing primary classes and execution logic
- Each file must have file_path, file_purpose, and a list of requirements
- Minimal, clean, modular design
- Output ONLY valid JSON


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

