from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.seed.steps import STEPS, run_step
from app.sse import stream

router = APIRouter(prefix="/api/seed", tags=["seed"])


@router.get("")
def list_steps() -> list[dict[str, Any]]:
    return [
        {"id": s.id, "title": s.title, "description": s.description, "requires": list(s.requires)}
        for s in STEPS.values()
    ]


@router.post("/{step_id}")
def run(step_id: str) -> StreamingResponse:
    """Run one seed step. Streams progress as server-sent events: start, log…, end."""
    if step_id not in STEPS:
        raise HTTPException(404, f"Unknown seed step '{step_id}'.")
    return stream(run_step(step_id))
