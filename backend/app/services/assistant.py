"""The support assistant: the RAG app whose quality the workshop investigates.

1. Fetch the prompt labelled `production` from Langfuse.
2. Retrieve from the Pinecone namespace named in that prompt's config.
3. Answer with whichever LLM provider is configured.
4. Log the trace, generation and prompt version back to Langfuse.
"""

import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.llm.types import LLMClient, Turn
from app.scenario import pinecone_index, prompt_name, trace_name
from app.services.knowledge_base import Hit, KnowledgeBase
from app.services.langfuse_api import LangfuseAPI, LangfuseError, iso


@dataclass
class Answer:
    answer: str
    prompt_version: int
    namespace: str
    sources: list[dict[str, Any]]
    trace_id: str
    trace_url: str
    model: str
    provider: str
    latency_ms: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compile_prompt(template: str, context: str, question: str) -> str:
    return template.replace("{{context}}", context).replace("{{question}}", question)


def format_context(hits: list[Hit]) -> str:
    return "\n\n".join(f"[{h.title}] (updated {h.updated})\n{h.text}" for h in hits) or "(none)"


async def ask(question: str, kb: KnowledgeBase, lf: LangfuseAPI, llm: LLMClient) -> Answer:
    prompt = await lf.get_prompt(prompt_name(), label="production")
    if prompt is None:
        raise LangfuseError(
            f"No production version of prompt '{prompt_name()}'. Run the Langfuse seed step."
        )
    config = prompt.get("config") or {}
    namespace = config.get("namespace", "")
    hits = await kb.search(namespace, question, top_k=int(config.get("top_k", 3)))
    system = compile_prompt(prompt["prompt"], format_context(hits), question)

    started = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    completion = await llm.complete(system=system, turns=[Turn(role="user", text=question)], max_tokens=2000)
    latency_ms = int((time.perf_counter() - t0) * 1000)

    trace_id = f"rca-live-{uuid.uuid4().hex[:12]}"
    metadata = {
        "prompt_name": prompt_name(),
        "prompt_version": prompt["version"],
        "pinecone_index": pinecone_index(),
        "pinecone_namespace": namespace,
        "retrieved_docs": [h.id for h in hits],
        "llm_provider": llm.provider,
    }
    await lf.ingest(
        [
            {
                "id": str(uuid.uuid4()),
                "type": "trace-create",
                "timestamp": iso(started),
                "body": {
                    "id": trace_id,
                    "timestamp": iso(started),
                    "name": trace_name(),
                    "input": {"question": question},
                    "output": {"answer": completion.text},
                    "release": f"{prompt_name()}@v{prompt['version']}",
                    "tags": ["live", f"prompt-v{prompt['version']}"],
                    "metadata": metadata,
                },
            },
            {
                "id": str(uuid.uuid4()),
                "type": "generation-create",
                "timestamp": iso(started),
                "body": {
                    "id": f"{trace_id}-answer",
                    "traceId": trace_id,
                    "name": "answer",
                    "startTime": iso(started),
                    "endTime": iso(started + timedelta(milliseconds=latency_ms)),
                    "model": completion.model,
                    "input": {"system": system, "question": question},
                    "output": completion.text,
                    "promptName": prompt_name(),
                    "promptVersion": prompt["version"],
                    "usageDetails": {
                        "input": completion.usage.input_tokens,
                        "output": completion.usage.output_tokens,
                    },
                    "metadata": metadata,
                },
            },
        ]
    )
    return Answer(
        answer=completion.text,
        prompt_version=prompt["version"],
        namespace=namespace,
        sources=[{"id": h.id, "title": h.title, "updated": h.updated, "score": h.score} for h in hits],
        trace_id=trace_id,
        trace_url=await lf.trace_url(trace_id),
        model=completion.model,
        provider=llm.provider,
        latency_ms=latency_ms,
    )


async def record_feedback(lf: LangfuseAPI, trace_id: str, helpful: bool) -> None:
    now = iso(datetime.now(timezone.utc))
    await lf.ingest(
        [
            {
                "id": str(uuid.uuid4()),
                "type": "score-create",
                "timestamp": now,
                "body": {
                    "id": f"{trace_id}-user-feedback",
                    "traceId": trace_id,
                    "name": "user_feedback",
                    "value": 1 if helpful else 0,
                    "dataType": "NUMERIC",
                },
            }
        ]
    )
