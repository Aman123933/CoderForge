from typing import Dict, Any, Optional


class OrchestratorAgent:
    """
    Central controller that coordinates all agents
    in the autonomous coding pipeline.
    """

    def __init__(
        self,
        *,
        intent_agent,
        planner_agent,
        architect_agent,
        coder_agent,
        reviewer_agent,
        runner_agent=None,
        max_code_retries: int = 1,
    ):
        self.intent_agent = intent_agent
        self.planner_agent = planner_agent
        self.architect_agent = architect_agent
        self.coder_agent = coder_agent
        self.reviewer_agent = reviewer_agent
        self.runner_agent = runner_agent
        self.max_code_retries = max_code_retries

    # --------------------------------------------------
    # PUBLIC ENTRYPOINT
    # --------------------------------------------------

    def run(self, user_input: str) -> Dict[str, Any]:
        """
        Executes the full autonomous pipeline except execution.
        """

        # 1️⃣ Intent Extraction
        intent = self.intent_agent.extract_intent(user_input)

        # 2️⃣ Planning
        plan = self.planner_agent.create_plan(intent)

        # 3️⃣ Architecture Design
        architecture = self.architect_agent.design_architecture(plan)

        # 4️⃣ Code Generation + Review Loop
        code, review = self._generate_and_review(architecture)

        # 5️⃣ Optional Execution (RunnerAgent)
        execution_result = None
        if self.runner_agent:
            execution_result = self.runner_agent.run(code)

        return {
            "intent": intent,
            "plan": plan,
            "architecture": architecture,
            "code": code,
            "review": review,
            "execution": execution_result,
        }

    # --------------------------------------------------
    # INTERNAL LOGIC
    # --------------------------------------------------

    def _generate_and_review(
        self,
        architecture: Dict[str, Any],
    ) -> tuple[str, Dict[str, Any]]:
        """
        Generates code and retries based on reviewer feedback.
        """

        attempt = 0
        last_review: Optional[Dict[str, Any]] = None

        file_spec = self._build_file_spec(architecture)

        while attempt <= self.max_code_retries:
            code = self.coder_agent.generate_code(file_spec)

            review = self.reviewer_agent.review_code(
                code=code,
                architecture_context=architecture,
            )

            if not review.get("issues"):
                return code, review

            last_review = review
            attempt += 1

        return code, last_review or {}

    # --------------------------------------------------
    # FILE SPEC STRATEGY
    # --------------------------------------------------

    def _build_file_spec(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts architecture into a single-file coding request.
        This is intentionally minimal and deterministic.
        """

        return {
            "file_path": "backend/app/main.py",
            "file_purpose": "Application entry point",
            "requirements": [
                "Initialize application",
                "Expose health endpoint",
            ],
        }
