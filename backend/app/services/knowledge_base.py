"""Every Pinecone call lives here.

The index uses Pinecone's integrated embedding model, so text goes in and text comes out:
no separate embedding provider is needed, whichever LLM provider you choose.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any

from pinecone import Pinecone

from app.scenario import KbArticle, scenario

TEXT_FIELD = "chunk_text"


@dataclass(frozen=True)
class Hit:
    id: str
    score: float
    title: str
    text: str
    updated: str


class KnowledgeBase:
    def __init__(self, api_key: str) -> None:
        self._pc = Pinecone(api_key=api_key, timeout=30.0)
        cfg = scenario()["pinecone"]
        self.index_name: str = cfg["index"]
        self._cfg = cfg

    def _ensure_index_sync(self) -> bool:
        """Create the index if needed. Returns True when it was created."""
        if self._pc.has_index(self.index_name):
            return False
        self._pc.create_index_for_model(
            name=self.index_name,
            cloud=self._cfg["cloud"],
            region=self._cfg["region"],
            embed={"model": self._cfg["embed_model"], "field_map": {"text": TEXT_FIELD}},
            tags={"project": "datahub-ai-rca"},
        )
        for _ in range(60):
            if self._pc.describe_index(self.index_name).status.get("ready"):
                break
            time.sleep(2)
        return True

    def _upsert_sync(self, namespace: str, articles: list[KbArticle]) -> int:
        index = self._pc.Index(self.index_name)
        records: list[dict[str, Any]] = [
            {
                "_id": a.id,
                TEXT_FIELD: f"{a.title}. {a.text}",
                "title": a.title,
                "updated": a.updated,
                "source": namespace,
            }
            for a in articles
        ]
        index.upsert_records(namespace=namespace, records=records)
        return len(records)

    def _wait_for_count_sync(self, expected: dict[str, int], timeout_s: int = 60) -> None:
        # Writes are eventually consistent; wait so the next step sees the vectors.
        index = self._pc.Index(self.index_name)
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            stats = index.describe_index_stats()
            counts = {ns: v.vector_count for ns, v in (stats.namespaces or {}).items()}
            if all(counts.get(ns, 0) >= n for ns, n in expected.items()):
                return
            time.sleep(2)

    def _search_sync(self, namespace: str, query: str, top_k: int) -> list[Hit]:
        index = self._pc.Index(self.index_name)
        response = index.search(
            namespace=namespace,
            query={"inputs": {"text": query}, "top_k": top_k},
            fields=[TEXT_FIELD, "title", "updated"],
        )
        hits = []
        for h in response.result.hits:
            fields = h.fields or {}
            hits.append(
                Hit(
                    id=h._id,
                    score=round(float(h._score), 4),
                    title=str(fields.get("title", "")),
                    text=str(fields.get(TEXT_FIELD, "")),
                    updated=str(fields.get("updated", "")),
                )
            )
        return hits

    def _stats_sync(self) -> dict[str, int]:
        if not self._pc.has_index(self.index_name):
            return {}
        stats = self._pc.Index(self.index_name).describe_index_stats()
        return {ns: v.vector_count for ns, v in (stats.namespaces or {}).items()}

    async def ensure_index(self) -> bool:
        return await asyncio.to_thread(self._ensure_index_sync)

    async def upsert(self, namespace: str, articles: list[KbArticle]) -> int:
        return await asyncio.to_thread(self._upsert_sync, namespace, articles)

    async def wait_for_counts(self, expected: dict[str, int]) -> None:
        await asyncio.to_thread(self._wait_for_count_sync, expected)

    async def search(self, namespace: str, query: str, top_k: int = 3) -> list[Hit]:
        return await asyncio.to_thread(self._search_sync, namespace, query, top_k)

    async def stats(self) -> dict[str, int]:
        return await asyncio.to_thread(self._stats_sync)
