import logging
from typing import Dict, Any, Optional, List, Set, Tuple


class OrchestratorAgent:
    """
    Central controller that coordinates all agents
    in the autonomous coding pipeline with self-correction and capped retries.
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
        max_code_retries: int = 3,
    ):
        self.intent_agent = intent_agent
        self.planner_agent = planner_agent
        self.architect_agent = architect_agent
        self.coder_agent = coder_agent
        self.reviewer_agent = reviewer_agent
        self.runner_agent = runner_agent
        self.max_code_retries = max_code_retries
        self.logger = logging.getLogger("OrchestratorAgent")

    # --------------------------------------------------
    # PUBLIC ENTRYPOINT
    # --------------------------------------------------

    def run(self, user_input: str) -> Dict[str, Any]:
        """
        Executes the full autonomous pipeline with multi-file generation,
        self-correction loop, and capped retries.
        """
        self.logger.info("Starting pipeline for input: %s", user_input[:80])

        # 1️⃣ Intent Extraction
        intent = self.intent_agent.extract_intent(user_input)

        # 2️⃣ Planning
        plan = self.planner_agent.create_plan(intent)

        # 3️⃣ Architecture Design
        architecture = self.architect_agent.design_architecture(plan)
        architecture["prompt"] = user_input

        # 4️⃣ Multi-file Generation + Self-Correction Review Loop
        generation_result = self._generate_and_review(architecture)
        project = generation_result["project"]
        manifest = generation_result["manifest"]
        final_review = generation_result["review"]
        attempts = generation_result["attempts"]
        retries_used = generation_result["retries_used"]

        # Primary single-file entrypoint for backwards compatibility
        entrypoint_file = manifest.get("entrypoint", "main.py")
        primary_code = project.get(entrypoint_file) or next(iter(project.values()), "")

        # 5️⃣ Optional Execution (RunnerAgent)
        execution_result = None
        has_major_issues = any(
            issue.get("severity") in {"critical", "major"}
            for issue in final_review.get("issues", [])
        )

        if self.runner_agent:
            if not has_major_issues:
                # Pass full project or primary code
                if hasattr(self.runner_agent, "run_project"):
                    execution_result = self.runner_agent.run_project(project, manifest=manifest)
                else:
                    execution_result = self.runner_agent.run(primary_code)
            else:
                self.logger.warning("Skipping execution due to unresolved major reviewer issues.")
                execution_result = {
                    "success": False,
                    "output": "",
                    "error": "Execution skipped: Reviewer reported critical/major issues.",
                    "exit_code": 1,
                    "duration": 0.0,
                }

        return {
            "intent": intent,
            "plan": plan,
            "architecture": architecture,
            "files": project,
            "project": project,
            "manifest": manifest,
            "code": primary_code,
            "review": final_review,
            "attempts": attempts,
            "retries_used": retries_used,
            "execution": execution_result,
        }

    # --------------------------------------------------
    # INTERNAL LOGIC
    # --------------------------------------------------

    def _generate_and_review(
        self,
        architecture: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generates project files and retries based on reviewer feedback,
        regenerating only affected files. Records every attempt.
        """
        file_specs = architecture.get("files") or self._build_file_specs(architecture)
        attempts: List[Dict[str, Any]] = []

        current_project: Dict[str, str] = {}
        last_review: Dict[str, Any] = {}
        manifest: Dict[str, Any] = {}

        attempt_idx = 0
        while attempt_idx <= self.max_code_retries:
            self.logger.info("Code generation attempt %d/%d", attempt_idx + 1, self.max_code_retries + 1)

            if attempt_idx == 0:
                # Initial full generation
                gen_res = self.coder_agent.generate_project(
                    file_specs=file_specs,
                    context=architecture,
                )
                current_project = gen_res["project"]
                manifest = gen_res["manifest"]
            else:
                # Self-correction: find affected files from previous review
                affected_files, feedback_by_file = self._find_affected_files(
                    last_review.get("issues", []),
                    current_project,
                )
                self.logger.info(
                    "Self-correcting attempt %d. Affected files: %s",
                    attempt_idx,
                    affected_files,
                )

                gen_res = self.coder_agent.generate_project(
                    file_specs=file_specs,
                    context=architecture,
                    existing_project=current_project,
                    affected_files=affected_files,
                    feedback_by_file=feedback_by_file,
                )
                current_project = gen_res["project"]
                manifest = gen_res["manifest"]

            # Review the current project
            if hasattr(self.reviewer_agent, "review_project"):
                review = self.reviewer_agent.review_project(
                    current_project,
                    architecture_context=architecture,
                )
            else:
                entrypoint = manifest.get("entrypoint", "main.py")
                code_to_review = current_project.get(entrypoint, "")
                review = self.reviewer_agent.review_code(
                    code=code_to_review,
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

            # Check if there are no major/critical issues to stop early
            has_blocking_issues = any(
                i.get("severity") in {"critical", "major"} for i in issues
            )
            if not issues or not has_blocking_issues:
                self.logger.info("Code generation succeeded on attempt %d with no blocking issues", attempt_idx + 1)
                break

            attempt_idx += 1

        return {
            "project": current_project,
            "manifest": manifest,
            "review": last_review,
            "attempts": attempts,
            "retries_used": max(0, len(attempts) - 1),
        }

    def _find_affected_files(
        self,
        issues: List[Dict[str, Any]],
        project: Dict[str, str],
    ) -> Tuple[Set[str], Dict[str, List[Dict[str, Any]]]]:
        """
        Maps reviewer issues to specific files.
        If an issue mentions a file in location or description, marks it.
        If no specific file can be identified, marks all files.
        """
        affected: Set[str] = set()
        feedback_by_file: Dict[str, List[Dict[str, Any]]] = {}

        for issue in issues:
            location = str(issue.get("location", "")).lower()
            desc = str(issue.get("description", "")).lower()
            matched_file = None

            for file_path in project.keys():
                path_lower = file_path.lower()
                basename = file_path.split("/")[-1].split("\\")[-1].lower()
                if path_lower in location or basename in location or path_lower in desc or basename in desc:
                    matched_file = file_path
                    break

            if matched_file:
                affected.add(matched_file)
                feedback_by_file.setdefault(matched_file, []).append(issue)
            else:
                # If cannot pinpoint, associate with all files
                for f in project.keys():
                    feedback_by_file.setdefault(f, []).append(issue)

        # If no specific files were matched, affect all project files
        if not affected:
            affected = set(project.keys())

        return affected, feedback_by_file

    def _build_file_specs(self, architecture: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fallback file spec builder if architecture has no files.
        """
        return [
            {
                "file_path": "main.py",
                "file_purpose": "Application entry point",
                "requirements": [
                    "Initialize application",
                    "Expose health endpoint",
                ],
            }
        ]

