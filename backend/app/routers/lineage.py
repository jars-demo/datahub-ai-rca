from typing import Any

from fastapi import APIRouter, HTTPException

from app import deps
from app.scenario import prompt_name
from app.services.datahub_api import DataHubError
from app.services.langfuse_api import LangfuseError
from app.services.lineage import build_graph

router = APIRouter(prefix="/api/lineage", tags=["lineage"])


@router.get("")
async def lineage() -> dict[str, Any]:
    """The scenario's AI lineage graph, read from DataHub."""
    production = None
    try:
        prompt = await deps.langfuse().get_prompt(prompt_name(), label="production")
        production = prompt["version"] if prompt else None
    except (LangfuseError, HTTPException):
        pass  # the graph still renders without knowing which version is live
    try:
        return await build_graph(deps.datahub(), production)
    except DataHubError as e:
        raise HTTPException(400, str(e)) from e
