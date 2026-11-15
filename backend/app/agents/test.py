from backend.app.llm.gemini_client import GeminiClient
from backend.app.agents.intent_agent import IntentExtractionAgent
from backend.app.agents.planner_agent import PlannerAgent
from backend.app.agents.architect_agent import ArchitectAgent
from backend.app.agents.coder_agent import CoderAgent
from backend.app.agents.reviewer_agent import ReviewerAgent
from backend.app.agents.runner_agent import RunnerAgent


llm = GeminiClient()

runner = RunnerAgent(
    intent_agent=IntentExtractionAgent(llm),
    planner_agent=PlannerAgent(llm),
    architect_agent=ArchitectAgent(llm),
    coder_agent=CoderAgent(llm),
    reviewer_agent=ReviewerAgent(llm),
)

result = runner.run("Build a todo app with authentication")

print("\n=== FINAL OUTPUT ===\n")
print(result)
