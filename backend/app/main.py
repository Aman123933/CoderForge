import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.agents.runner_agent import RunnerAgent
from backend.app.agents.intent_agent import IntentExtractionAgent
from backend.app.agents.planner_agent import PlannerAgent
from backend.app.agents.architect_agent import ArchitectAgent
from backend.app.agents.coder_agent import CoderAgent
from backend.app.agents.reviewer_agent import ReviewerAgent

from backend.app.llm.gemini_client import GeminiClient
from backend.app.tools.logging_tools import setup_logger
from backend.app.api import routes

# ----------------------------
# App & Logger
# ----------------------------

app = FastAPI(title="CodeForge - Autonomous Multi-Agent Code Generation")
logger = setup_logger()

# ----------------------------
# CORS Middleware
# ----------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# LLM + Agents Initialization
# ----------------------------

try:
    llm = GeminiClient()
    runner = RunnerAgent(
        intent_agent=IntentExtractionAgent(llm),
        planner_agent=PlannerAgent(llm),
        architect_agent=ArchitectAgent(llm),
        coder_agent=CoderAgent(llm),
        reviewer_agent=ReviewerAgent(llm),
    )
    routes.set_runner(runner)
except Exception as e:
    logger.warning("Default GeminiClient initialization skipped (e.g. running offline or without key): %s", e)
    runner = None

# ----------------------------
# Include Routes
# ----------------------------

# Mount routes under /api and root
app.include_router(routes.router, prefix="/api")
app.include_router(routes.router)


# ----------------------------
# Direct Routes for backwards compatibility
# ----------------------------

class RunRequest(BaseModel):
    prompt: str


@app.get("/health")
def health():
    return {"status": "ok"}
