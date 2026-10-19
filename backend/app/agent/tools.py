"""The agent's tools. All read-only. Each returns plain JSON-able data with DataHub links,
so any model can cite its evidence."""

from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from statistics import mean
from typing import Any

from app.llm.types import ToolSpec
from app.scenario import namespaces, prompt_name, scenario, trace_name
from app.services.datahub_api import DataHubAPI
from app.services.knowledge_base import KnowledgeBase
from app.services.langfuse_api import LangfuseAPI
from app.services.lineage import prompt_urn

Handler = Callable[[dict[str, Any]], Awaitable[Any]]
SCORE_NAMES = scenario()["langfuse"]["scores"]


@dataclass
class ToolContext:
    langfuse: LangfuseAPI
    datahub: DataHubAPI
    kb: KnowledgeBase
    _traces: dict[int, list[dict[str, Any]]] = field(default_factory=dict)
    _scores: dict[tuple[str, int], list[dict[str, Any]]] = field(default_factory=dict)

    async def traces(self, days: int) -> list[dict[str, Any]]:
        if days not in self._traces:
            self._traces[days] = await self.langfuse.traces(trace_name(), days)
        return self._traces[days]

    async def scores(self, name: str, days: int) -> list[dict[str, Any]]:
        if (name, days) not in self._scores:
            self._scores[(name, days)] = await self.langfuse.scores(name, days)
        return self._scores[(name, days)]

    async def scored_traces(self, score_name: str, days: int) -> list[dict[str, Any]]:
        by_trace = {s["traceId"]: s["value"] for s in await self.scores(score_name, days)}
        rows = []
        for t in await self.traces(days):
            meta = t.get("metadata") or {}
            if t["id"] in by_trace and meta.get("prompt_version") is not None:
                rows.append(
                    {
                        "trace_id": t["id"],
                        "timestamp": t["timestamp"],
                        "prompt_version": int(meta["prompt_version"]),
                        "namespace": meta.get("pinecone_namespace"),
                        "question": (t.get("input") or {}).get("question"),
                        "answer": (t.get("output") or {}).get("answer"),
                        "score": by_trace[t["id"]],
                    }
                )
        return sorted(rows, key=lambda r: r["timestamp"])


def _with_url(ctx: ToolContext, entity: dict[str, Any]) -> dict[str, Any]:
    keep = (
        "urn",
        "name",
        "platform",
        "subtypes",
        "description",
        "owners",
        "deprecated",
        "deprecation_note",
        "tags",
        "domain",
        "degree",
    )
    return {
        **{k: entity[k] for k in keep if k in entity},
        "url": ctx.datahub.entity_url(entity["urn"], entity.get("type")),
    }


async def quality_trend(ctx: ToolContext, args: dict[str, Any]) -> Any:
    score_name = args.get("score_name", "correctness")
    days = int(args.get("days", 7))
    rows = await ctx.scored_traces(score_name, days)
    daily: dict[tuple[str, int], list[float]] = defaultdict(list)
    per_version: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        daily[(r["timestamp"][:10], r["prompt_version"])].append(r["score"])
        per_version[r["prompt_version"]].append(r)
    return {
        "score": score_name,
        "days": days,
        "traces": len(rows),
        "daily": [
            {"date": d, "prompt_version": v, "avg": round(mean(s), 3), "n": len(s)}
            for (d, v), s in sorted(daily.items())
        ],
        "by_prompt_version": [
            {
                "prompt_version": v,
                "avg": round(mean(r["score"] for r in rs), 3),
                "n": len(rs),
                "namespaces": sorted({r["namespace"] for r in rs if r["namespace"]}),
                "first_seen": rs[0]["timestamp"],
                "last_seen": rs[-1]["timestamp"],
            }
            for v, rs in sorted(per_version.items())
        ],
    }


async def list_prompt_versions(ctx: ToolContext, args: dict[str, Any]) -> Any:
    name = prompt_name()
    versions = await ctx.langfuse.prompt_versions(name)
    usage: dict[int, list[str]] = defaultdict(list)
    for t in await ctx.traces(14):
        v = (t.get("metadata") or {}).get("prompt_version")
        if v is not None:
            usage[int(v)].append(t["timestamp"])
    return {
        "prompt": name,
        "langfuse_url": await ctx.langfuse.prompt_url(name),
        "versions": [
            {
                "version": p["version"],
                "labels": p.get("labels", []),
                "commit_message": p.get("commitMessage"),
                "config": p.get("config"),
                "traces_last_14d": len(usage[p["version"]]),
                "first_seen_in_traffic": min(usage[p["version"]], default=None),
                "datahub_urn": prompt_urn(p["version"]),
                "datahub_url": ctx.datahub.entity_url(prompt_urn(p["version"])),
            }
            for p in versions
        ],
        "note": "Deployment time is when a version first appears in traffic.",
    }


async def low_scoring_examples(ctx: ToolContext, args: dict[str, Any]) -> Any:
    score_name = args.get("score_name", "correctness")
    threshold = float(args.get("max_score", 0.5))
    limit = min(int(args.get("limit", 5)), 10)
    rows = [r for r in await ctx.scored_traces(score_name, 7) if r["score"] <= threshold]
    return {
        "score": score_name,
        "max_score": threshold,
        "matching": len(rows),
        "examples": [
            {**r, "langfuse_url": await ctx.langfuse.trace_url(r["trace_id"])} for r in rows[-limit:]
        ],
    }


async def datahub_search(ctx: ToolContext, args: dict[str, Any]) -> Any:
    results = await ctx.datahub.search(args.get("query", "*"), args.get("platform"))
    return {"results": [_with_url(ctx, e) for e in results]}


async def datahub_entity(ctx: ToolContext, args: dict[str, Any]) -> Any:
    entity = await ctx.datahub.entity(args["urn"])
    return _with_url(ctx, entity) if entity else {"error": f"No entity {args['urn']} in DataHub."}


async def datahub_lineage(ctx: ToolContext, args: dict[str, Any]) -> Any:
    total, items = await ctx.datahub.lineage(
        args["urn"], args.get("direction", "UPSTREAM"), int(args.get("max_hops", 1))
    )
    return {
        "urn": args["urn"],
        "direction": args.get("direction", "UPSTREAM"),
        "total": total,
        "entities": [_with_url(ctx, e) for e in items[:25]],
    }


async def knowledge_base_lookup(ctx: ToolContext, args: dict[str, Any]) -> Any:
    hits = await ctx.kb.search(args["namespace"], args["query"], top_k=2)
    return {
        "namespace": args["namespace"],
        "hits": [{"id": h.id, "title": h.title, "updated": h.updated, "text": h.text} for h in hits],
    }


_NS = list(namespaces().values())

TOOLS: dict[str, tuple[ToolSpec, Callable[[ToolContext, dict[str, Any]], Awaitable[Any]]]] = {
    spec.name: (spec, fn)
    for spec, fn in (
        (
            ToolSpec(
                "quality_trend",
                "Daily average of a Langfuse evaluation score for the support assistant, split "
                "by prompt version, plus per-version averages and when each version first and "
                "last appeared in traffic. Start here to see whether and when quality changed.",
                {
                    "type": "object",
                    "properties": {
                        "score_name": {"type": "string", "enum": SCORE_NAMES},
                        "days": {"type": "integer", "minimum": 1, "maximum": 14},
                    },
                    "required": ["score_name"],
                },
            ),
            quality_trend,
        ),
        (
            ToolSpec(
                "prompt_versions",
                "All versions of the assistant's Langfuse prompt: labels (which is in "
                "production), commit message, config (including the Pinecone namespace it "
                "retrieves from), traffic counts and the matching DataHub URN.",
                {"type": "object", "properties": {}},
            ),
            list_prompt_versions,
        ),
        (
            ToolSpec(
                "low_scoring_examples",
                "Recent traces whose score is at or below a threshold, with the question, the "
                "answer, the prompt version and the namespace used.",
                {
                    "type": "object",
                    "properties": {
                        "score_name": {"type": "string", "enum": SCORE_NAMES},
                        "max_score": {"type": "number"},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 10},
                    },
                    "required": ["score_name"],
                },
            ),
            low_scoring_examples,
        ),
        (
            ToolSpec(
                "datahub_search",
                "Search the DataHub catalog. Optionally restrict to a platform: 's3' (source "
                "documents), 'pinecone' (vector indexes and namespaces) or 'langfuse' (prompt "
                "versions, traces).",
                {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "platform": {"type": "string", "enum": ["s3", "pinecone", "langfuse"]},
                    },
                    "required": ["query"],
                },
            ),
            datahub_search,
        ),
        (
            ToolSpec(
                "datahub_entity",
                "Details of one DataHub entity by URN: description, owners, deprecation status "
                "and note, tags, domain and a link to it in DataHub.",
                {
                    "type": "object",
                    "properties": {"urn": {"type": "string"}},
                    "required": ["urn"],
                },
            ),
            datahub_entity,
        ),
        (
            ToolSpec(
                "datahub_lineage",
                "Entities upstream (where data comes from) or downstream (what depends on it) "
                "of a DataHub entity. Use UPSTREAM from a prompt version to find the vector "
                "namespace and the source documents behind it.",
                {
                    "type": "object",
                    "properties": {
                        "urn": {"type": "string"},
                        "direction": {"type": "string", "enum": ["UPSTREAM", "DOWNSTREAM"]},
                        "max_hops": {"type": "integer", "minimum": 1, "maximum": 3},
                    },
                    "required": ["urn", "direction"],
                },
            ),
            datahub_lineage,
        ),
        (
            ToolSpec(
                "knowledge_base_lookup",
                "Search one Pinecone namespace and return the best matching articles. Use it to "
                "compare what two namespaces say about the same topic.",
                {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string", "enum": _NS},
                        "query": {"type": "string"},
                    },
                    "required": ["namespace", "query"],
                },
            ),
            knowledge_base_lookup,
        ),
    )
}
