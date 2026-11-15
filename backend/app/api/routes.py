from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class RunRequest(BaseModel):
    prompt: str


@router.post("/run")
def run_agent(request: RunRequest):
    return {"message": "wire runner here later"}
