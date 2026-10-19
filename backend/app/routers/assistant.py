from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app import deps
from app.llm.types import LLMError
from app.scenario import prompt_name, prompt_versions, seed_questions
from app.services import assistant
from app.services.knowledge_base import KnowledgeBase
from app.services.langfuse_api import LangfuseError

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class FeedbackRequest(BaseModel):
    trace_id: str
    helpful: bool


class ProductionRequest(BaseModel):
    version: int = Field(ge=1)


@router.get("/examples")
def examples() -> list[str]:
    return [q.question for q in seed_questions() if q.changed][:6]


@router.post("/ask")
async def ask(body: AskRequest) -> dict[str, Any]:
    """Ask the support assistant. Uses the production prompt from Langfuse, retrieves from
    Pinecone, answers with the configured LLM and logs a trace to Langfuse."""
    kb: KnowledgeBase = deps.knowledge_base()
    lf = deps.langfuse()
    llm = deps.llm()
    try:
        answer = await assistant.ask(body.question, kb, lf, llm)
    except (LLMError, LangfuseError) as e:
        raise HTTPException(400, str(e)) from e
    return answer.to_dict()


@router.post("/feedback", status_code=204)
async def feedback(body: FeedbackRequest) -> None:
    try:
        await assistant.record_feedback(deps.langfuse(), body.trace_id, body.helpful)
    except LangfuseError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/prompt")
async def prompt_state() -> dict[str, Any]:
    """Which prompt version is in production, and the namespace each version retrieves from."""
    lf = deps.langfuse()
    try:
        versions = await lf.prompt_versions(prompt_name())
    except LangfuseError as e:
        raise HTTPException(400, str(e)) from e
    return {
        "name": prompt_name(),
        "url": await lf.prompt_url(prompt_name()) if versions else None,
        "versions": [
            {
                "version": v["version"],
                "labels": v.get("labels", []),
                "commit_message": v.get("commitMessage"),
                "namespace": (v.get("config") or {}).get("namespace"),
            }
            for v in versions
        ],
    }


@router.post("/prompt/production")
async def set_production(body: ProductionRequest) -> dict[str, Any]:
    """Move the `production` label to a version: the fix (roll back to v2) or a reset (v3)."""
    lf = deps.langfuse()
    try:
        await lf.set_labels(prompt_name(), body.version, ["production"])
    except LangfuseError as e:
        raise HTTPException(400, str(e)) from e
    return await prompt_state()


@router.get("/scenario")
def scenario_versions() -> list[dict[str, Any]]:
    return [
        {"version": p.version, "namespace": p.config["namespace"], "commit_message": p.commit_message}
        for p in prompt_versions()
    ]
