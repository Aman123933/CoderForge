from typing import Dict, Any, Optional
from backend.app.memory.state_store import StateStore
from backend.app.tools.execution_tools import SafePythonExecutor
from backend.app.agents.orchestrator_agent import OrchestratorAgent


class RunnerAgent:
    """
    Runner Agent that coordinates pipeline execution, state persistence,
    and sandboxed subprocess execution.
    """

    def __init__(
        self,
        intent_agent,
        planner_agent,
        architect_agent,
        coder_agent,
        reviewer_agent,
        max_code_retries: int = 3,
        timeout: float = 10.0,
    ):
        self.intent_agent = intent_agent
        self.planner_agent = planner_agent
        self.architect_agent = architect_agent
        self.coder_agent = coder_agent
        self.reviewer_agent = reviewer_agent
        self.max_code_retries = max_code_retries
        self.memory = StateStore()
        self.executor = SafePythonExecutor(timeout=timeout)
        self.orchestrator = OrchestratorAgent(
            intent_agent=self.intent_agent,
            planner_agent=self.planner_agent,
            architect_agent=self.architect_agent,
            coder_agent=self.coder_agent,
            reviewer_agent=self.reviewer_agent,
            runner_agent=self,
            max_code_retries=self.max_code_retries,
        )

    def run(self, user_prompt: str) -> Dict[str, Any]:
        """
        Executes the entire multi-agent pipeline from user prompt to sandboxed execution.
        """
        self.memory.clear()
        self.memory.set("prompt", user_prompt)

        # 1. Intent Extraction
        intent = self.intent_agent.extract_intent(user_prompt)
        self.memory.set("intent", intent)

        # 2. Planning
        plan = self.planner_agent.create_plan(intent)
        self.memory.set("plan", plan)

        # 3. Architecture Design
        architecture = self.architect_agent.design_architecture(plan)
        self.memory.set("architecture", architecture)

        # 4. Multi-file generation + self-correction review loop
        generation_res = self.orchestrator._generate_and_review(architecture)
        project = generation_res["project"]
        manifest = generation_res["manifest"]
        review = generation_res["review"]
        attempts = generation_res["attempts"]
        retries_used = generation_res["retries_used"]

        entrypoint = manifest.get("entrypoint", "main.py")
        code = project.get(entrypoint) or next(iter(project.values()), "")

        self.memory.set("project", project)
        self.memory.set("files", project)
        self.memory.set("manifest", manifest)
        self.memory.set("code", code)
        self.memory.set("review", review)
        self.memory.set("attempts", attempts)
        self.memory.set("retries_used", retries_used)

        # 5. Real Execution in Subprocess
        # Run only if the Reviewer reports no major or critical issues
        issues = review.get("issues", [])
        has_major_issues = any(
            i.get("severity") in {"critical", "major"} for i in issues
        )

        if not has_major_issues:
            execution_result = self.executor.execute_project(project, manifest=manifest)
            self.memory.set("execution", execution_result)
        else:
            skipped_result = {
                "success": False,
                "output": "",
                "stderr": "Execution skipped: Unresolved critical or major reviewer issues.",
                "exit_code": 1,
                "duration": 0.0,
                "error": "Execution skipped due to reviewer issues.",
            }
            self.memory.set("execution", skipped_result)

        return self.memory.all()

    def run_project(
        self,
        project: Dict[str, str],
        manifest: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Directly executes a generated project in sandboxed subprocess.
        """
        return self.executor.execute_project(project, manifest=manifest)

