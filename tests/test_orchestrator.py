import pytest
from backend.app.agents.orchestrator_agent import OrchestratorAgent


class DummyIntent:
    def extract_intent(self, p):
        return {
            "intent": "build_application",
            "app_type": "cli",
            "backend_required": True,
            "frontend_required": False,
            "features": ["task_crud"],
            "constraints": [],
            "assumptions": [],
        }


class DummyPlanner:
    def create_plan(self, i):
        return {
            "project_name": "task_cli",
            "steps": ["Setup project", "Implement handlers"],
        }


class DummyArchitect:
    def design_architecture(self, p):
        return {
            "system_overview": "CLI Task system",
            "backend_components": ["main", "storage"],
            "frontend_components": [],
            "data_models": ["Task"],
            "integration_points": [],
            "external_dependencies": [],
            "files": [
                {
                    "file_path": "main.py",
                    "file_purpose": "Entry point",
                    "requirements": ["Run CLI"],
                },
                {
                    "file_path": "storage.py",
                    "file_purpose": "Storage helper",
                    "requirements": ["Save tasks"],
                },
            ],
        }


class MockCoder:
    def __init__(self):
        self.call_count = 0
        self.regenerated_files = []

    def generate_project(
        self,
        file_specs,
        context=None,
        existing_project=None,
        affected_files=None,
        feedback_by_file=None,
    ):
        self.call_count += 1
        project = dict(existing_project or {})

        for spec in file_specs:
            path = spec["file_path"]
            if affected_files is not None and path not in affected_files and path in project:
                continue
            self.regenerated_files.append((self.call_count, path))
            project[path] = f"# Implementation for {path} (v{self.call_count})"

        return {
            "project": project,
            "manifest": {
                "file_count": len(project),
                "files": list(project.keys()),
                "entrypoint": "main.py",
            },
        }


class MockReviewer:
    def __init__(self, issues_per_call):
        self.issues_per_call = list(issues_per_call)
        self.calls = 0

    def review_project(self, project, architecture_context=None):
        self.calls += 1
        if self.issues_per_call:
            issues = self.issues_per_call.pop(0)
        else:
            issues = []
        return {
            "summary": "Review summary",
            "issues": issues,
            "recommendations": [],
        }


def test_orchestrator_retry_cap():
    coder = MockCoder()
    # Continuous major issue: should stop at max_code_retries
    reviewer = MockReviewer([
        [{"severity": "major", "description": "Syntax error in main.py", "location": "main.py"}],
        [{"severity": "major", "description": "Still broken", "location": "main.py"}],
        [{"severity": "major", "description": "Still broken", "location": "main.py"}],
        [{"severity": "major", "description": "Still broken", "location": "main.py"}],
    ])

    orch = OrchestratorAgent(
        intent_agent=DummyIntent(),
        planner_agent=DummyPlanner(),
        architect_agent=DummyArchitect(),
        coder_agent=coder,
        reviewer_agent=reviewer,
        max_code_retries=2,
    )

    result = orch.run("Build a CLI app")
    # 1 initial + 2 retries = 3 attempts total
    assert len(result["attempts"]) == 3
    assert result["retries_used"] == 2
    assert coder.call_count == 3


def test_orchestrator_early_exit_on_success():
    coder = MockCoder()
    reviewer = MockReviewer([
        [{"severity": "major", "description": "Error in storage.py", "location": "storage.py"}],
        [],  # Second attempt fixes everything
    ])

    orch = OrchestratorAgent(
        intent_agent=DummyIntent(),
        planner_agent=DummyPlanner(),
        architect_agent=DummyArchitect(),
        coder_agent=coder,
        reviewer_agent=reviewer,
        max_code_retries=3,
    )

    result = orch.run("Build a CLI app")
    assert len(result["attempts"]) == 2
    assert result["retries_used"] == 1
    assert result["review"]["issues"] == []


def test_orchestrator_selective_file_regeneration():
    coder = MockCoder()
    reviewer = MockReviewer([
        [{"severity": "major", "description": "Error in storage.py", "location": "storage.py"}],
        [],
    ])

    orch = OrchestratorAgent(
        intent_agent=DummyIntent(),
        planner_agent=DummyPlanner(),
        architect_agent=DummyArchitect(),
        coder_agent=coder,
        reviewer_agent=reviewer,
        max_code_retries=3,
    )

    orch.run("Build a CLI app")
    # Call 1 generated both main.py and storage.py
    # Call 2 should only regenerate storage.py
    call2_regenerated = [path for c, path in coder.regenerated_files if c == 2]
    assert "storage.py" in call2_regenerated
    assert "main.py" not in call2_regenerated
