"""The workshop scenario, loaded from data/. Shared with the ingestion package."""

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from app.settings import DATA_DIR


@dataclass(frozen=True)
class KbArticle:
    id: str
    title: str
    updated: str
    text: str


@dataclass(frozen=True)
class PromptVersion:
    version: int
    commit_message: str
    labels: list[str]
    config: dict[str, Any]
    prompt: str


@dataclass(frozen=True)
class SeedQuestion:
    doc: str
    question: str
    current: str
    archive: str

    @property
    def changed(self) -> bool:
        return self.current != self.archive


def _load(path: str) -> Any:
    return json.loads((DATA_DIR / path).read_text())


@lru_cache
def scenario() -> dict[str, Any]:
    return _load("scenario.json")


def pinecone_index() -> str:
    return scenario()["pinecone"]["index"]


def namespaces() -> dict[str, str]:
    return scenario()["pinecone"]["namespaces"]


def prompt_name() -> str:
    return scenario()["langfuse"]["prompt_name"]


def trace_name() -> str:
    return scenario()["langfuse"]["trace_name"]


@lru_cache
def kb_articles() -> dict[str, list[KbArticle]]:
    """Articles per namespace."""
    ns = namespaces()
    return {
        ns["current"]: [KbArticle(**a) for a in _load("kb/help-center-2025.json")],
        ns["archive"]: [KbArticle(**a) for a in _load("kb/help-center-2023-archive.json")],
    }


@lru_cache
def prompt_versions() -> list[PromptVersion]:
    return [PromptVersion(**p) for p in _load("langfuse/prompts.json")]


@lru_cache
def seed_questions() -> list[SeedQuestion]:
    return [SeedQuestion(**q) for q in _load("langfuse/questions.json")]
