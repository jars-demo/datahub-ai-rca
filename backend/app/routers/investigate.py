from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app import deps
from app.agent.runner import investigate
from app.agent.tools import ToolContext
from app.sse import stream

router = APIRouter(prefix="/api/investigate", tags=["investigate"])

SUGGESTIONS = [
    "Why did the support assistant's answer quality drop this week?",
    "Which data is behind the prompt version that is in production, and who owns it?",
    "Are any customer-facing answers based on deprecated data?",
]


class InvestigateRequest(BaseModel):
    question: str = Field(min_length=5, max_length=1000)


@router.get("/suggestions")
def suggestions() -> list[str]:
    return SUGGESTIONS


@router.post("")
def run(body: InvestigateRequest) -> StreamingResponse:
    """Run the root-cause agent. Streams events: start, note, tool_call, tool_result, answer,
    done (or error)."""
    llm = deps.llm()
    ctx = ToolContext(langfuse=deps.langfuse(), datahub=deps.datahub(), kb=deps.knowledge_base())

    async def events() -> AsyncIterator[dict[str, Any]]:
        async for e in investigate(body.question, llm, ctx):
            yield e

    return stream(events())
