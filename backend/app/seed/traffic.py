"""Generates a deterministic week of support-assistant traffic for Langfuse.

Until `regression_days_ago`, prompt v2 is live and retrieves from the 2025 help center.
After that, v3 is live and retrieves from the 2023 archive, so answers about anything that
changed since 2023 are confidently wrong and their correctness scores drop.
"""

import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.scenario import pinecone_index, prompt_name, prompt_versions, scenario, seed_questions, trace_name
from app.services.langfuse_api import iso

SEED_TAG = "seeded"
_NAMESPACE_UUID = uuid.UUID("5d1c3a6e-7c0b-4b8e-9a51-1f0d2c9e4b11")


@dataclass(frozen=True)
class SeededTrace:
    id: str
    timestamp: datetime
    prompt_version: int
    namespace: str
    question: str
    answer: str
    scores: dict[str, float]


def _event_id(*parts: str) -> str:
    # Stable event ids: re-seeding sends the same events instead of new ones.
    return str(uuid.uuid5(_NAMESPACE_UUID, "/".join(parts)))


def generate(now: datetime | None = None, seed: int = 42) -> list[SeededTrace]:
    cfg = scenario()["langfuse"]
    rng = random.Random(seed)
    now = (now or datetime.now(timezone.utc)).replace(minute=0, second=0, microsecond=0)
    regression_at = now - timedelta(days=cfg["regression_days_ago"])
    namespace_by_version = {p.version: p.config["namespace"] for p in prompt_versions()}
    questions = seed_questions()

    traces = []
    for day in range(cfg["seed_days"], 0, -1):
        day_start = (now - timedelta(days=day)).replace(hour=0)
        for i in range(cfg["traces_per_day"]):
            ts = day_start + timedelta(hours=8 + i, minutes=rng.randint(0, 59))
            version = 3 if ts >= regression_at else 2
            q = rng.choice(questions)
            wrong = version == 3 and q.changed
            traces.append(
                SeededTrace(
                    id=f"rca-seed-{day}-{i}",
                    timestamp=ts,
                    prompt_version=version,
                    namespace=namespace_by_version[version],
                    question=q.question,
                    answer=q.archive if version == 3 else q.current,
                    scores={
                        "correctness": round(
                            rng.uniform(0.1, 0.35) if wrong else rng.uniform(0.84, 0.98), 2
                        ),
                        "helpfulness": round(
                            rng.uniform(0.4, 0.6) if wrong else rng.uniform(0.8, 0.96), 2
                        ),
                    },
                )
            )
    return traces


def to_events(traces: list[SeededTrace], model_label: str) -> list[dict[str, Any]]:
    index = pinecone_index()
    name = prompt_name()
    events: list[dict[str, Any]] = []
    for t in traces:
        gen_id = f"{t.id}-answer"
        metadata = {
            "prompt_name": name,
            "prompt_version": t.prompt_version,
            "pinecone_index": index,
            "pinecone_namespace": t.namespace,
            "seeded": True,
        }
        events.append(
            {
                "id": _event_id(t.id, "trace"),
                "type": "trace-create",
                "timestamp": iso(t.timestamp),
                "body": {
                    "id": t.id,
                    "timestamp": iso(t.timestamp),
                    "name": trace_name(),
                    "input": {"question": t.question},
                    "output": {"answer": t.answer},
                    "release": f"{name}@v{t.prompt_version}",
                    "tags": [SEED_TAG, f"prompt-v{t.prompt_version}"],
                    "metadata": metadata,
                },
            }
        )
        events.append(
            {
                "id": _event_id(t.id, "generation"),
                "type": "generation-create",
                "timestamp": iso(t.timestamp),
                "body": {
                    "id": gen_id,
                    "traceId": t.id,
                    "name": "answer",
                    "startTime": iso(t.timestamp),
                    "endTime": iso(t.timestamp + timedelta(seconds=2)),
                    "model": model_label,
                    "input": {"question": t.question, "namespace": t.namespace},
                    "output": t.answer,
                    "promptName": name,
                    "promptVersion": t.prompt_version,
                    "metadata": metadata,
                },
            }
        )
        for score_name, value in t.scores.items():
            events.append(
                {
                    "id": _event_id(t.id, score_name),
                    "type": "score-create",
                    "timestamp": iso(t.timestamp),
                    "body": {
                        "id": f"{t.id}-{score_name}",
                        "traceId": t.id,
                        "name": score_name,
                        "value": value,
                        "dataType": "NUMERIC",
                        "comment": "Seeded evaluation score",
                    },
                }
            )
    return events
