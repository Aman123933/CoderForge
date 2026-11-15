import uuid
from typing import Dict, Any, Optional
from backend.app.memory.state_store import StateStore
from backend.app.tools.execution_tools import SafePythonExecutor
from backend.app.agents.orchestrator_agent import OrchestratorAgent
from backend.app.tools.metrics_collector import MetricsCollector


class RunnerAgent:
    """
    Runner Agent that coordinates pipeline execution, state persistence,
    metrics instrumentation, and sandboxed subprocess execution.
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

    def run(self, user_prompt: str, run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the entire multi-agent pipeline from user prompt to sandboxed execution,
        capturing detailed per-agent latency, tokens, retries, and execution metrics.
        """
        run_id = run_id or str(uuid.uuid4())
        metrics = MetricsCollector(run_id=run_id, prompt=user_prompt)

        self.memory.clear()
        self.memory.set("run_id", run_id)
        self.memory.set("prompt", user_prompt)

        # 1. Intent Extraction
        with metrics.measure("intent"):
            intent = self.intent_agent.extract_intent(user_prompt)
        self.memory.set("intent", intent)

        # 2. Planning
        with metrics.measure("planner"):
            plan = self.planner_agent.create_plan(intent)
        self.memory.set("plan", plan)

        # 3. Architecture Design
        with metrics.measure("architect"):
            architecture = self.architect_agent.design_architecture(plan)
        self.memory.set("architecture", architecture)

        # 4. Multi-file generation + self-correction review loop
        # We time coder and reviewer inside orchestrator
        generation_res = self._timed_generate_and_review(architecture, metrics)
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

        # Record reviewer attempts into metrics
        metrics.record_attempts(attempts)

        # 5. Real Execution in Subprocess
        # Run only if the Reviewer reports no major or critical issues
        issues = review.get("issues", [])
        has_major_issues = any(
            i.get("severity") in {"critical", "major"} for i in issues
        )

        execution_result = None
        if not has_major_issues:
            with metrics.measure("runner"):
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

        # Extract LLM usage if available from any agent's client
        llm = getattr(self.coder_agent, "llm", None) or getattr(self.intent_agent, "llm", None)
        metrics_record = metrics.finish(
            files_count=len(project),
            execution_result=execution_result,
            llm=llm,
        )
        self.memory.set("metrics", metrics_record)

        return self.memory.all()

    def _timed_generate_and_review(
        self,
        architecture: Dict[str, Any],
        metrics: MetricsCollector,
    ) -> Dict[str, Any]:
        """
        Runs generation and review while attributing time to coder and reviewer.
        """
        file_specs = architecture.get("files") or self.orchestrator._build_file_specs(architecture)
        attempts = []
        current_project = {}
        last_review = {}
        manifest = {}

        attempt_idx = 0
        while attempt_idx <= self.max_code_retries:
            if attempt_idx == 0:
                with metrics.measure("coder"):
                    gen_res = self.coder_agent.generate_project(
                        file_specs=file_specs,
                        context=architecture,
                    )
            else:
                affected_files, feedback_by_file = self.orchestrator._find_affected_files(
                    last_review.get("issues", []),
                    current_project,
                )
                with metrics.measure("coder"):
                    gen_res = self.coder_agent.generate_project(
                        file_specs=file_specs,
                        context=architecture,
                        existing_project=current_project,
                        affected_files=affected_files,
                        feedback_by_file=feedback_by_file,
                    )

            current_project = gen_res["project"]
            manifest = gen_res["manifest"]

            with metrics.measure("reviewer"):
                if hasattr(self.reviewer_agent, "review_project"):
                    review = self.reviewer_agent.review_project(
                        current_project,
                        architecture_context=architecture,
                    )
                else:
                    entrypoint = manifest.get("entrypoint", "main.py")
                    review = self.reviewer_agent.review_code(
                        code=current_project.get(entrypoint, ""),
                        architecture_context=architecture,
                    )

            last_review = review
            issues = review.get("issues", [])
            issues_summary = {
                "critical": sum(1 for i in issues if i.get("severity") == "critical"),
                "major": sum(1 for i in issues if i.get("severity") == "major"),
                "minor": sum(1 for i in issues if i.get("severity") == "minor"),
                "total": len(issues),
            }

            attempts.append({
                "attempt": attempt_idx + 1,
                "project": dict(current_project),
                "review": review,
                "issues_count": issues_summary,
            })

            has_blocking_issues = any(
                i.get("severity") in {"critical", "major"} for i in issues
            )
            if not issues or not has_blocking_issues:
                break

            attempt_idx += 1

        return {
            "project": current_project,
            "manifest": manifest,
            "review": last_review,
            "attempts": attempts,
            "retries_used": max(0, len(attempts) - 1),
        }

    def run_project(
        self,
        project: Dict[str, str],
        manifest: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Directly executes a generated project in sandboxed subprocess.
        """
        return self.executor.execute_project(project, manifest=manifest)


