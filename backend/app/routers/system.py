import asyncio
import json
from typing import Any

from fastapi import APIRouter, HTTPException

from app import deps
from app.connectors.registry import CONNECTORS
from app.services.datahub_api import DataHubAPI, DataHubError
from app.settings import INGESTION_DIR

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/about")
async def about() -> dict[str, Any]:
    """What this build runs on: the live DataHub server version and commit, and where the
    Pinecone and Langfuse connectors come from."""
    build = json.loads((INGESTION_DIR / "BUILD_INFO.json").read_text())
    values = deps.get_store().resolve(CONNECTORS["datahub"], {})
    server: dict[str, Any] = {"gms_url": values["gms_url"], "reachable": False}
    try:
        config = await DataHubAPI(values["gms_url"], "", values.get("ui_url", "")).server_config()
        info = config.get("versions", {}).get("acryldata/datahub", {})
        server.update(
            reachable=True,
            version=info.get("version"),
            commit=info.get("commit"),
            commit_url=f"https://github.com/datahub-project/datahub/commit/{info.get('commit')}"
            if info.get("commit")
            else None,
            server_type=(config.get("datahub") or {}).get("serverType"),
        )
    except DataHubError as e:
        server["error"] = str(e)
    return {"datahub_server": server, **build}


@router.get("/status")
async def status() -> dict[str, Any]:
    """One call for the UI: which connections are configured and which seed steps are done."""
    from app.seed.steps import STEPS

    store = deps.get_store()
    connections = {
        cid: {
            "configured": not c.missing_required(store.resolve(c, {})),
            "ok": (store.get(cid).last_check or None) is not None and store.get(cid).last_check.ok,
        }
        for cid, c in CONNECTORS.items()
    }

    async def step_status(step_id: str) -> str:
        step = STEPS[step_id]
        if not all(connections[r]["configured"] for r in step.requires):
            return "blocked"
        try:
            return await asyncio.wait_for(step.status(), timeout=20)
        except (HTTPException, Exception):  # noqa: BLE001 - status is best effort
            return "unknown"

    results = await asyncio.gather(*(step_status(s) for s in STEPS))
    return {"connections": connections, "seed": dict(zip(STEPS, results, strict=True))}
