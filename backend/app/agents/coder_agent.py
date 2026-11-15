import re
from typing import Any, Dict, List, Optional, Set
from backend.app.agents.base_agent import BaseAgent


class CoderAgent(BaseAgent):
    """
    Generates code for structured file specifications.
    Can generate single files or loop over an architect's file list to generate a full project.
    """

    def __init__(self, llm):
        super().__init__(
            llm,
            agent_name="CoderAgent",
            require_json=False,  # code is NOT JSON
        )

    def generate_code(
        self,
        file_spec: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        feedback: Optional[List[Dict[str, Any]]] = None,
        current_code: Optional[str] = None,
    ) -> str:
        self._validate_file_spec(file_spec)

        prompt = self._build_prompt(
            file_spec,
            context=context,
            feedback=feedback,
            current_code=current_code,
        )
        raw_code = self.call_llm(prompt)
        return self._clean_code(raw_code)

    def generate_project(
        self,
        file_specs: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        existing_project: Optional[Dict[str, str]] = None,
        affected_files: Optional[Set[str]] = None,
        feedback_by_file: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> Dict[str, Any]:
        """
        Loops over the file list, calling the LLM once per file,
        returning a project (dict of path -> code) plus a manifest.
        If affected_files is provided, only regenerates those files.
        """
        project: Dict[str, str] = dict(existing_project or {})
        feedback_map = feedback_by_file or {}

        for spec in file_specs:
            file_path = spec.get("file_path", "")

            # If selective regeneration is requested and this file is unaffected, keep existing
            if affected_files is not None and file_path not in affected_files and file_path in project:
                self.logger.info("Skipping unaffected file: %s", file_path)
                continue

            self.logger.info("Generating code for file: %s", file_path)
            file_feedback = feedback_map.get(file_path, [])
            current_code = project.get(file_path)

            code = self.generate_code(
                spec,
                context=context,
                feedback=file_feedback if file_feedback else None,
                current_code=current_code,
            )
            project[file_path] = code

        manifest = {
            "file_count": len(project),
            "files": list(project.keys()),
            "entrypoint": self._detect_entrypoint(list(project.keys())),
        }

        return {
            "project": project,
            "manifest": manifest,
        }

    def _validate_file_spec(self, file_spec: Dict[str, Any]) -> None:
        required_keys = {"file_path", "file_purpose", "requirements"}
        missing = required_keys - file_spec.keys()

        if missing:
            raise ValueError(f"Missing keys in file_spec: {missing}")

        if not isinstance(file_spec["requirements"], list):
            raise ValueError("requirements must be a list")

    def _build_prompt(
        self,
        file_spec: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        feedback: Optional[List[Dict[str, Any]]] = None,
        current_code: Optional[str] = None,
    ) -> str:
        requirements_text = "\n".join(
            f"- {req}" for req in file_spec["requirements"]
        )

        context_block = ""
        if context:
            context_block = f"""
PROJECT CONTEXT:
System Overview: {context.get("system_overview", "")}
Data Models: {context.get("data_models", [])}
Other Files: {[f.get("file_path") for f in context.get("files", []) if isinstance(f, dict)]}
"""

        correction_block = ""
        if feedback and current_code:
            issues_text = "\n".join(
                f"- [{i.get('severity', 'major')}] {i.get('description', '')} (at {i.get('location', '')})"
                for i in feedback
            )
            correction_block = f"""
SELF-CORRECTION FEEDBACK:
Previous implementation had the following issues that MUST be fixed:
{issues_text}

PREVIOUS CODE TO IMPROVE:
{current_code}
"""

        return f"""
You are a CODER AGENT acting as a senior software engineer.

⚠️ STRICT RULES ⚠️
- Generate code for EXACTLY ONE FILE.
- Do NOT create folders.
- Do NOT reference files that are not mentioned.
- Do NOT explain anything.
- Do NOT use markdown prose. Return executable Python code only.
- Output ONLY valid, complete, working code.

FILE PATH:
{file_spec["file_path"]}

FILE PURPOSE:
{file_spec["file_purpose"]}

REQUIREMENTS:
{requirements_text}
{context_block}
{correction_block}
"""

    def _clean_code(self, raw_code: str) -> str:
        code = raw_code.strip()
        # Remove ```python ... ``` fences if present
        if code.startswith("```"):
            lines = code.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines).strip()
        return code

    def _detect_entrypoint(self, file_paths: List[str]) -> str:
        for candidate in ["main.py", "app.py", "run.py", "backend/app/main.py"]:
            for path in file_paths:
                if path.endswith(candidate) or path == candidate:
                    return path
        return file_paths[0] if file_paths else "main.py"



