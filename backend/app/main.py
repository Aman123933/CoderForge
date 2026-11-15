from fastapi import FastAPI
from pydantic import BaseModel

from backend.app.agents.runner_agent import RunnerAgent
from backend.app.agents.intent_agent import IntentExtractionAgent
from backend.app.agents.planner_agent import PlannerAgent
from backend.app.agents.architect_agent import ArchitectAgent
from backend.app.agents.coder_agent import CoderAgent
from backend.app.agents.reviewer_agent import ReviewerAgent

from backend.app.llm.gemini_client import GeminiClient
from backend.app.tools.logging_tools import setup_logger


# ----------------------------
# App & Logger
# ----------------------------

app = FastAPI(title="AI Autonomous Coder")
logger = setup_logger()


# ----------------------------
# LLM + Agents Initialization
# ----------------------------

llm = GeminiClient()

runner = RunnerAgent(
    intent_agent=IntentExtractionAgent(llm),
    planner_agent=PlannerAgent(llm),
    architect_agent=ArchitectAgent(llm),
    coder_agent=CoderAgent(llm),
    reviewer_agent=ReviewerAgent(llm),
)


# ----------------------------
# Request / Response Models
# ----------------------------

class RunRequest(BaseModel):
    prompt: str


# ----------------------------
# Routes
# ----------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run")
def run_agent(request: RunRequest):
    logger.info("Received run request")
    result = runner.run(request.prompt)
    logger.info("Run completed")
    return result
