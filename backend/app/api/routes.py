import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.app.memory.run_store import RunStore

router = APIRouter()
run_store = RunStore()

# Global runner instance will be injected from main.py or initialized lazily
_runner_instance = None


def set_runner(runner):
    global _runner_instance
    _runner_instance = runner


def get_runner():
    global _runner_instance
    if _runner_instance is None:
        from backend.app.llm.gemini_client import GeminiClient
        from backend.app.agents.runner_agent import RunnerAgent
        from backend.app.agents.intent_agent import IntentExtractionAgent
        from backend.app.agents.planner_agent import PlannerAgent
        from backend.app.agents.architect_agent import ArchitectAgent
        from backend.app.agents.coder_agent import CoderAgent
        from backend.app.agents.reviewer_agent import ReviewerAgent

        llm = GeminiClient()
        _runner_instance = RunnerAgent(
            intent_agent=IntentExtractionAgent(llm),
            planner_agent=PlannerAgent(llm),
            architect_agent=ArchitectAgent(llm),
            coder_agent=CoderAgent(llm),
            reviewer_agent=ReviewerAgent(llm),
        )
    return _runner_instance


class RunRequest(BaseModel):
    prompt: str


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/run")
def run_pipeline(request: RunRequest):
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    runner = get_runner()
    run_id = str(uuid.uuid4())

    try:
        result = runner.run(request.prompt)
        # Store in run store
        run_record = run_store.save_run(
            run_id=run_id,
            prompt=request.prompt,
            data=result,
            metrics=result.get("metrics"),
            status="completed",
        )
        return {
            "run_id": run_id,
            "status": "completed",
            "result": result,
            "record": run_record,
        }
    except Exception as e:
        error_data = {"error": str(e)}
        run_store.save_run(
            run_id=run_id,
            prompt=request.prompt,
            data=error_data,
            status="failed",
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs")
def list_runs(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    return {
        "runs": run_store.list_runs(limit=limit, offset=offset),
        "limit": limit,
        "offset": offset,
    }


@router.get("/runs/{run_id}")
def get_run(run_id: str):
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return run
