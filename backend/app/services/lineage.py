"""The AI lineage graph, read back from DataHub: source data → Pinecone namespace → Langfuse
prompt version → production traffic."""

import asyncio
from typing import Any

from app.scenario import pinecone_index, prompt_name, prompt_versions, scenario
from app.services.datahub_api import DataHubAPI

STAGES = ["source", "vector", "prompt"]


def dataset_urn(platform: str, name: str) -> str:
    return f"urn:li:dataset:(urn:li:dataPlatform:{platform},{name},PROD)"


def prompt_urn(version: int) -> str:
    return dataset_urn("langfuse", f"{prompt_name()}.v{version}")


def namespace_urn(namespace: str) -> str:
    return dataset_urn("pinecone", f"{pinecone_index()}.{namespace}")


def _stage(platform: str | None) -> str:
    return {"langfuse": "prompt", "pinecone": "vector"}.get(platform or "", "source")


async def build_graph(dh: DataHubAPI, production_version: int | None) -> dict[str, Any]:
    """Nodes and edges for every scenario prompt version and everything upstream of it."""
    nodes: dict[str, dict[str, Any]] = {}
    edges: set[tuple[str, str]] = set()

    async def visit_prompt(version: int) -> None:
        urn = prompt_urn(version)
        entity = await dh.entity(urn)
        if entity is None:
            return
        # Downstream of a prompt version are the Langfuse traces and generations that used it.
        traffic, _ = await dh.lineage(urn, "DOWNSTREAM", max_hops=1, count=1)
        nodes[urn] = {
            **entity,
            "stage": "prompt",
            "version": version,
            "production": version == production_version,
            "traffic": traffic,
        }
        # Walk upstream one hop at a time so edges are exact.
        frontier = [urn]
        for _ in range(3):
            next_frontier = []
            for child in frontier:
                _, parents = await dh.lineage(child, "UPSTREAM", max_hops=1)
                for parent in parents:
                    edges.add((parent["urn"], child))
                    if parent["urn"] not in nodes:
                        nodes[parent["urn"]] = {**parent, "stage": _stage(parent["platform"])}
                        next_frontier.append(parent["urn"])
            frontier = next_frontier

    await asyncio.gather(*(visit_prompt(p.version) for p in prompt_versions()))
    for node in nodes.values():
        node["url"] = dh.entity_url(node["urn"], node.get("type"))
    return {
        "stages": STAGES,
        "nodes": sorted(nodes.values(), key=lambda n: (STAGES.index(n["stage"]), n["name"])),
        "edges": [{"source": s, "target": t} for s, t in sorted(edges)],
        "domain": scenario()["datahub"]["domain"],
    }
