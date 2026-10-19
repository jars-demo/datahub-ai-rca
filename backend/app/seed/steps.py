"""The seeding steps. Each one streams log lines, so the workshop UI and the CLI show the same
progress. All steps are idempotent: run them again at any time to reset the scenario."""

import asyncio
import os
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal

from app import deps
from app.scenario import kb_articles, namespaces, prompt_name, prompt_versions, trace_name
from app.seed import traffic
from app.services.lineage import prompt_urn
from app.settings import INGESTION_DIR, get_settings

Log = dict[str, Any]
StepStatus = Literal["done", "pending", "unknown"]


def log(message: str, level: str = "info") -> Log:
    return {"type": "log", "level": level, "message": message}


# ---- Pinecone ----------------------------------------------------------


async def seed_pinecone() -> AsyncIterator[Log]:
    kb = deps.knowledge_base()
    yield log(f"Ensuring index '{kb.index_name}' (integrated embedding model)…")
    if await kb.ensure_index():
        yield log("Created the index.")
    else:
        yield log("Index already exists.")
    expected = {}
    for namespace, articles in kb_articles().items():
        count = await kb.upsert(namespace, articles)
        expected[namespace] = count
        yield log(f"Upserted {count} articles into namespace '{namespace}'.")
    yield log("Waiting for vectors to become searchable…")
    await kb.wait_for_counts(expected)
    yield log(f"Pinecone ready: {await kb.stats()}", "success")


async def pinecone_status() -> StepStatus:
    stats = await deps.knowledge_base().stats()
    expected = {ns: len(a) for ns, a in kb_articles().items()}
    return "done" if all(stats.get(ns, 0) >= n for ns, n in expected.items()) else "pending"


# ---- Langfuse ----------------------------------------------------------


async def ensure_prompts() -> AsyncIterator[Log]:
    lf = deps.langfuse()
    name = prompt_name()
    existing = await lf.prompt_versions(name)
    wanted = prompt_versions()
    for p in wanted[len(existing) :]:
        created = await lf.create_prompt(name, p.prompt, p.config, p.labels, p.commit_message)
        yield log(f"Created prompt '{name}' v{created.get('version')}: {p.commit_message}")
    if len(existing) >= len(wanted):
        yield log(f"Prompt '{name}' already has {len(existing)} versions.")
    # The scenario starts with the regressed version in production.
    await lf.set_labels(name, wanted[-1].version, ["production"])
    yield log(f"Label 'production' → v{wanted[-1].version}.")


async def seed_langfuse() -> AsyncIterator[Log]:
    async for line in ensure_prompts():
        yield line
    lf = deps.langfuse()
    traces = traffic.generate()
    model_label = "seeded"
    try:
        model_label = deps.llm().model
    except Exception:  # noqa: BLE001 - the label is cosmetic; seeding works without an LLM
        pass
    events = traffic.to_events(traces, model_label)
    regressed = sum(1 for t in traces if t.prompt_version == 3)
    yield log(
        f"Sending {len(traces)} traces over {len({t.timestamp.date() for t in traces})} days "
        f"({regressed} on v3) with generations and scores…"
    )
    sent = await lf.ingest(events)
    yield log(f"Langfuse accepted {sent} events.", "success")
    yield log(f"Open the prompt: {await lf.prompt_url(prompt_name())}")


async def langfuse_status() -> StepStatus:
    lf = deps.langfuse()
    versions = await lf.prompt_versions(prompt_name())
    if len(versions) < len(prompt_versions()):
        return "pending"
    return "done" if await lf.traces(trace_name(), days=8) else "pending"


# ---- DataHub -----------------------------------------------------------


def _ingestion_env() -> dict[str, str]:
    store = deps.get_store()
    dh = deps.connection_values("datahub", store)
    pc = deps.connection_values("pinecone", store)
    lf = deps.connection_values("langfuse", store)
    # Credentials go only into the child process's environment, which is how DataHub
    # recipes resolve ${VARS}; they never touch this process's environment.
    return {
        **os.environ,
        "DATAHUB_GMS_URL": dh["gms_url"],
        "DATAHUB_TOKEN": dh["token"],
        "PINECONE_API_KEY": pc["api_key"],
        "LANGFUSE_HOST": lf["host"],
        "LANGFUSE_PUBLIC_KEY": lf["public_key"],
        "LANGFUSE_SECRET_KEY": lf["secret_key"],
        "DATAHUB_TELEMETRY_ENABLED": "false",
        "PYTHONUNBUFFERED": "1",
    }


async def _run_ingestion(step: str, env: dict[str, str]) -> AsyncIterator[Log]:
    python = get_settings().ingestion_python
    if not python.exists():
        yield log(f"Ingestion environment not found at {python}. Run `make setup`.", "error")
        raise RuntimeError("ingestion environment missing")
    proc = await asyncio.create_subprocess_exec(
        str(python), "-m", "rca_ingestion.run", step,
        cwd=INGESTION_DIR,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    assert proc.stdout is not None
    async for raw in proc.stdout:
        line = raw.decode(errors="replace").rstrip()
        if line:
            yield log(line, "detail")
    if await proc.wait() != 0:
        raise RuntimeError(f"ingestion step '{step}' failed")


async def seed_datahub() -> AsyncIterator[Log]:
    env = _ingestion_env()
    for step, title in (
        ("pinecone", "Pinecone source (DataHub connector, PR #16472)"),
        ("langfuse", "Langfuse source (PR #19923, bundled)"),
        ("context", "Source datasets, owners and lineage"),
    ):
        yield log(f"Ingesting: {title}…")
        async for line in _run_ingestion(step, env):
            yield line
        yield log(f"Done: {title}.", "success")


async def datahub_status() -> StepStatus:
    dh = deps.datahub()
    latest = prompt_versions()[-1].version
    entity = await dh.entity(prompt_urn(latest))
    if not entity or not entity.get("owners"):
        return "pending"
    total, _ = await dh.lineage(prompt_urn(latest), "UPSTREAM", max_hops=1, count=1)
    return "done" if total > 0 else "pending"


# ---- registry ----------------------------------------------------------


@dataclass(frozen=True)
class SeedStep:
    id: str
    title: str
    description: str
    requires: tuple[str, ...]
    run: Callable[[], AsyncIterator[Log]]
    status: Callable[[], Awaitable[StepStatus]]


STEPS: dict[str, SeedStep] = {
    s.id: s
    for s in (
        SeedStep(
            "pinecone",
            "Seed the knowledge base",
            f"Create the index and embed two help-center versions into "
            f"'{namespaces()['current']}' and '{namespaces()['archive']}'.",
            ("pinecone",),
            seed_pinecone,
            pinecone_status,
        ),
        SeedStep(
            "langfuse",
            "Seed a week of traffic",
            "Create prompt versions v1–v3 and a week of traces with generations and scores.",
            ("langfuse",),
            seed_langfuse,
            langfuse_status,
        ),
        SeedStep(
            "datahub",
            "Load it all into DataHub",
            "Run the Pinecone and Langfuse connectors, then add sources, owners and lineage.",
            ("datahub", "pinecone", "langfuse"),
            seed_datahub,
            datahub_status,
        ),
    )
}


async def run_step(step_id: str) -> AsyncIterator[Log]:
    step = STEPS[step_id]
    yield {"type": "start", "step": step_id}
    try:
        async for line in step.run():
            yield line
    except Exception as e:  # noqa: BLE001 - surfaced to the user as the step's result
        detail = getattr(e, "detail", None) or str(e)
        yield log(str(detail), "error")
        yield {"type": "end", "step": step_id, "ok": False}
        return
    yield {"type": "end", "step": step_id, "ok": True}
