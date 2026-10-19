"""Builds service clients from the saved connection settings."""

from functools import lru_cache

from fastapi import HTTPException

from app.connectors.registry import CONNECTORS
from app.llm.factory import build_llm
from app.llm.types import LLMClient, LLMError
from app.services.datahub_api import DataHubAPI
from app.services.knowledge_base import KnowledgeBase
from app.services.langfuse_api import LangfuseAPI
from app.settings import get_settings, read_env
from app.store import ConnectionStore


@lru_cache
def get_store() -> ConnectionStore:
    settings = get_settings()
    return ConnectionStore(settings.connections_file, env=read_env(settings))


class NotConfigured(HTTPException):
    def __init__(self, connector_id: str, missing: list[str]) -> None:
        name = CONNECTORS[connector_id].name
        super().__init__(
            status_code=400,
            detail=f"{name} is not configured (missing: {', '.join(missing)}). "
            "Open Connections to set it up.",
        )


def connection_values(connector_id: str, store: ConnectionStore | None = None) -> dict[str, str]:
    connector = CONNECTORS[connector_id]
    values = (store or get_store()).resolve(connector, {})
    missing = connector.missing_required(values)
    if missing:
        raise NotConfigured(connector_id, missing)
    return values


def knowledge_base() -> KnowledgeBase:
    return KnowledgeBase(connection_values("pinecone")["api_key"])


def langfuse() -> LangfuseAPI:
    v = connection_values("langfuse")
    return LangfuseAPI(v["host"], v["public_key"], v["secret_key"])


def datahub() -> DataHubAPI:
    v = connection_values("datahub")
    return DataHubAPI(v["gms_url"], v["token"], v.get("ui_url", ""))


def llm() -> LLMClient:
    try:
        return build_llm(connection_values("llm"))
    except LLMError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
