"""Every Langfuse call lives here (public REST API, basic auth with the project key pair)."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import quote

import httpx


class LangfuseError(Exception):
    pass


def iso(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class LangfuseAPI:
    def __init__(self, host: str, public_key: str, secret_key: str) -> None:
        self.host = host.rstrip("/")
        self._auth = (public_key, secret_key)
        self._project_id: Optional[str] = None

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Any = None,
        allow_404: bool = False,
    ) -> Any:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.request(
                    method, f"{self.host}{path}", params=params, json=json, auth=self._auth
                )
            except httpx.HTTPError as e:
                raise LangfuseError(f"Could not reach Langfuse at {self.host}: {e}") from e
        if allow_404 and resp.status_code == 404:
            return None
        if resp.status_code in (401, 403):
            raise LangfuseError("Langfuse rejected the key pair.")
        if resp.status_code >= 400:
            raise LangfuseError(f"Langfuse {method} {path} failed ({resp.status_code}): {resp.text[:300]}")
        return resp.json() if resp.content else None

    # ---- project -------------------------------------------------------

    async def project_id(self) -> str:
        if self._project_id is None:
            data = await self._request("GET", "/api/public/projects")
            projects = data.get("data", [])
            if not projects:
                raise LangfuseError("No Langfuse project found for this key pair.")
            self._project_id = projects[0]["id"]
        return self._project_id

    async def trace_url(self, trace_id: str) -> str:
        return f"{self.host}/project/{await self.project_id()}/traces/{quote(trace_id)}"

    async def prompt_url(self, name: str) -> str:
        return f"{self.host}/project/{await self.project_id()}/prompts/{quote(name)}"

    # ---- prompts -------------------------------------------------------

    async def get_prompt(
        self, name: str, *, version: Optional[int] = None, label: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        params: dict[str, Any] = {}
        if version is not None:
            params["version"] = version
        elif label:
            params["label"] = label
        return await self._request(
            "GET", f"/api/public/v2/prompts/{quote(name, safe='')}", params=params, allow_404=True
        )

    async def prompt_versions(self, name: str) -> list[dict[str, Any]]:
        """All versions of a prompt, oldest first."""
        listing = await self._request("GET", "/api/public/v2/prompts", params={"name": name})
        meta = next((p for p in listing.get("data", []) if p.get("name") == name), None)
        if meta is None:
            return []
        versions = []
        for v in sorted(meta.get("versions", [])):
            prompt = await self.get_prompt(name, version=v)
            if prompt:
                versions.append(prompt)
        return versions

    async def create_prompt(
        self,
        name: str,
        prompt: str,
        config: dict[str, Any],
        labels: list[str],
        commit_message: str,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/public/v2/prompts",
            json={
                "name": name,
                "type": "text",
                "prompt": prompt,
                "config": config,
                "labels": labels,
                "tags": ["datahub-ai-rca"],
                "commitMessage": commit_message,
            },
        )

    async def set_labels(self, name: str, version: int, labels: list[str]) -> dict[str, Any]:
        """Assign labels to a version. A label such as 'production' moves off other versions."""
        return await self._request(
            "PATCH",
            f"/api/public/v2/prompts/{quote(name, safe='')}/versions/{version}",
            json={"newLabels": labels},
        )

    # ---- ingestion -----------------------------------------------------

    async def ingest(self, events: list[dict[str, Any]], batch_size: int = 100) -> int:
        """Send trace/generation/score events. Same ids upsert, so re-seeding is idempotent."""
        sent = 0
        for i in range(0, len(events), batch_size):
            batch = events[i : i + batch_size]
            result = await self._request("POST", "/api/public/ingestion", json={"batch": batch})
            errors = (result or {}).get("errors", [])
            if errors:
                raise LangfuseError(f"Langfuse rejected {len(errors)} events: {errors[0]}")
            sent += len(batch)
        return sent

    # ---- reading traffic -----------------------------------------------

    async def _paged(self, path: str, params: dict[str, Any], max_pages: int = 20) -> list[dict]:
        items: list[dict] = []
        for page in range(1, max_pages + 1):
            data = await self._request("GET", path, params={**params, "page": page, "limit": 100})
            if data is None:
                break
            items += data.get("data", [])
            if page >= (data.get("meta") or {}).get("totalPages", 1):
                break
        return items

    async def traces(self, name: str, days: int) -> list[dict[str, Any]]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        return await self._paged(
            "/api/public/traces", {"name": name, "fromTimestamp": iso(since)}
        )

    async def scores(self, name: str, days: int) -> list[dict[str, Any]]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        params = {"name": name, "fromTimestamp": iso(since)}
        try:
            return await self._paged("/api/public/v2/scores", params)
        except LangfuseError:
            # Older self-hosted Langfuse versions only have the v1 endpoint.
            return await self._paged("/api/public/scores", params)
