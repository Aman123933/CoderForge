import pytest
from backend.app.agents.intent_agent import IntentExtractionAgent
from backend.app.agents.planner_agent import PlannerAgent
from backend.app.agents.architect_agent import ArchitectAgent
from backend.app.agents.coder_agent import CoderAgent
from backend.app.agents.reviewer_agent import ReviewerAgent
from backend.app.agents.runner_agent import RunnerAgent
from backend.app.agents.base_agent import BaseAgent


class StaticLLM:
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.call_count = 1
        self.cumulative_usage = {"input_tokens": 10, "output_tokens": 10, "total_tokens": 20}

    def generate(self, prompt: str) -> str:
        return self.response_text

    def get_usage(self):
        return {"llm_calls": self.call_count, "cumulative_usage": self.cumulative_usage}


def test_intent_agent():
    intent_json = (
        '{\n'
        '  "intent": "build_application",\n'
        '  "app_type": "cli",\n'
        '  "backend_required": true,\n'
        '  "frontend_required": false,\n'
        '  "features": ["create task", "delete task"],\n'
        '  "constraints": [],\n'
        '  "assumptions": []\n'
        '}'
    )
    agent = IntentExtractionAgent(StaticLLM(intent_json))
    res = agent.extract_intent("Build a todo app")
    assert res["intent"] == "build_application"
    assert res["backend_required"] is True
    assert res["features"] == ["task_crud"]


def test_planner_agent():
    plan_json = '{\n  "project_name": "todo_app",\n  "steps": ["Step 1", "Step 2"]\n}'
    agent = PlannerAgent(StaticLLM(plan_json))
    res = agent.create_plan({"intent": "build"})
    assert res["project_name"] == "todo_app"
    assert len(res["steps"]) == 2


def test_architect_agent():
    arch_json = (
        '{\n'
        '  "system_overview": "Overview",\n'
        '  "backend_components": ["API", "DB"],\n'
        '  "frontend_components": [],\n'
        '  "data_models": ["Task"],\n'
        '  "integration_points": [],\n'
        '  "external_dependencies": [],\n'
        '  "files": [\n'
        '    {"file_path": "main.py", "file_purpose": "Entry", "requirements": ["init"]}\n'
        '  ]\n'
        '}'
    )
    agent = ArchitectAgent(StaticLLM(arch_json))
    res = agent.design_architecture({"project_name": "todo"})
    assert "main.py" in [f["file_path"] for f in res["files"]]


def test_coder_agent_single_and_project():
    code_text = "def app():\n    return 'running'\n"
    agent = CoderAgent(StaticLLM(code_text))
    spec = {"file_path": "main.py", "file_purpose": "Entry", "requirements": ["init"]}
    single = agent.generate_code(spec)
    assert "def app" in single

    project_res = agent.generate_project([spec])
    assert "main.py" in project_res["project"]
    assert project_res["manifest"]["file_count"] == 1


def test_reviewer_agent():
    review_json = (
        '{\n'
        '  "summary": "Clean code",\n'
        '  "issues": [\n'
        '    {"severity": "minor", "description": "Add comments", "location": "main.py"}\n'
        '  ],\n'
        '  "recommendations": ["Improve docstrings"]\n'
        '}'
    )
    agent = ReviewerAgent(StaticLLM(review_json))
    review = agent.review_project({"main.py": "print(1)"})
    assert review["summary"] == "Clean code"
    assert len(review["issues"]) == 1


def test_runner_agent_full_mock_flow():
    intent_llm = StaticLLM('{"intent": "build", "app_type": "cli", "backend_required": true, "frontend_required": false, "features": [], "constraints": [], "assumptions": []}')
    plan_llm = StaticLLM('{"project_name": "cli_tool", "steps": ["s1"]}')
    arch_llm = StaticLLM('{"system_overview": "CLI", "backend_components": ["main"], "frontend_components": [], "data_models": [], "integration_points": [], "external_dependencies": [], "files": [{"file_path": "main.py", "file_purpose": "entry", "requirements": ["run"]}]}')
    coder_llm = StaticLLM('print("FULL_FLOW_SUCCESS")')
    reviewer_llm = StaticLLM('{"summary": "ok", "issues": [], "recommendations": []}')

    runner = RunnerAgent(
        intent_agent=IntentExtractionAgent(intent_llm),
        planner_agent=PlannerAgent(plan_llm),
        architect_agent=ArchitectAgent(arch_llm),
        coder_agent=CoderAgent(coder_llm),
        reviewer_agent=ReviewerAgent(reviewer_llm),
    )

    result = runner.run("Build CLI tool")
    assert result["execution"]["success"] is True
    assert "FULL_FLOW_SUCCESS" in result["execution"]["output"]
    assert "metrics" in result
    assert result["metrics"]["execution_success"] is True
