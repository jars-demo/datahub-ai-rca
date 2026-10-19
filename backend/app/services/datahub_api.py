"""Every DataHub call lives here: GraphQL on GMS for reads, and the frontend login for creating
a personal access token in a fresh quickstart."""

from typing import Any, Optional
from urllib.parse import quote

import httpx

_ENTITY_FIELDS = """
  urn
  type
  ... on Dataset {
    name
    platform { name }
    properties { name description customProperties { key value } }
    editableProperties { description }
    subTypes { typeNames }
    deprecation { deprecated note }
    ownership { owners { owner {
      ... on CorpGroup { name properties { displayName } }
      ... on CorpUser { username properties { displayName } }
    } } }
    globalTags { tags { tag { name } } }
    domain { domain { properties { name } } }
  }
  ... on DataProcessInstance { name }
  ... on Container { properties { name description } platform { name } }
"""

_SEARCH = """
query search($input: SearchAcrossEntitiesInput!) {
  searchAcrossEntities(input: $input) {
    total
    searchResults { entity { %s } }
  }
}
""" % _ENTITY_FIELDS

_ENTITY = """
query entity($urn: String!) { entity(urn: $urn) { %s } }
""" % _ENTITY_FIELDS

_LINEAGE = """
query lineage($input: SearchAcrossLineageInput!) {
  searchAcrossLineage(input: $input) {
    total
    searchResults { degree entity { %s } }
  }
}
""" % _ENTITY_FIELDS

_CREATE_TOKEN = """
mutation createToken($input: CreateAccessTokenInput!) {
  createAccessToken(input: $input) { accessToken }
}
"""


class DataHubError(Exception):
    pass


def summarize(entity: dict[str, Any]) -> dict[str, Any]:
    """Flatten a GraphQL entity into the fields the agent and UI need."""
    props = entity.get("properties") or {}
    editable = entity.get("editableProperties") or {}
    owners = [
        (o["owner"].get("properties") or {}).get("displayName")
        or o["owner"].get("name")
        or o["owner"].get("username")
        for o in ((entity.get("ownership") or {}).get("owners") or [])
    ]
    deprecation = entity.get("deprecation") or {}
    return {
        "urn": entity["urn"],
        "type": entity.get("type"),
        "name": props.get("name") or entity.get("name") or entity["urn"],
        "platform": (entity.get("platform") or {}).get("name"),
        "subtypes": (entity.get("subTypes") or {}).get("typeNames") or [],
        "description": editable.get("description") or props.get("description") or "",
        "owners": [o for o in owners if o],
        "deprecated": bool(deprecation.get("deprecated")),
        "deprecation_note": deprecation.get("note") or "",
        "tags": [t["tag"]["name"] for t in ((entity.get("globalTags") or {}).get("tags") or [])],
        "domain": (((entity.get("domain") or {}).get("domain") or {}).get("properties") or {}).get(
            "name"
        ),
        "custom_properties": {
            p["key"]: p["value"] for p in (props.get("customProperties") or [])
        },
    }


class DataHubAPI:
    def __init__(self, gms_url: str, token: str, ui_url: str) -> None:
        self.gms_url = gms_url.rstrip("/")
        self.ui_url = ui_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}"} if token else {}

    def entity_url(self, urn: str, entity_type: Optional[str] = None) -> str:
        path = {
            "DATASET": "dataset",
            "CONTAINER": "container",
            "DATA_PROCESS_INSTANCE": "dataProcessInstance",
        }.get((entity_type or "DATASET").upper(), "dataset")
        return f"{self.ui_url}/{path}/{quote(urn, safe='')}"

    async def graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(
                    f"{self.gms_url}/api/graphql",
                    json={"query": query, "variables": variables},
                    headers=self._headers,
                )
            except httpx.HTTPError as e:
                raise DataHubError(f"Could not reach DataHub at {self.gms_url}: {e}") from e
        if resp.status_code in (401, 403):
            raise DataHubError("DataHub rejected the access token.")
        if resp.status_code != 200:
            raise DataHubError(f"DataHub GraphQL error ({resp.status_code}).")
        body = resp.json()
        if body.get("errors"):
            raise DataHubError(f"DataHub GraphQL error: {body['errors'][0].get('message')}")
        return body["data"]

    async def server_config(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(f"{self.gms_url}/config")
            except httpx.HTTPError as e:
                raise DataHubError(f"Could not reach DataHub at {self.gms_url}: {e}") from e
        if resp.status_code != 200:
            raise DataHubError(f"DataHub /config returned {resp.status_code}.")
        return resp.json()

    async def search(
        self, query: str, platform: Optional[str] = None, count: int = 10
    ) -> list[dict[str, Any]]:
        search_input: dict[str, Any] = {"query": query or "*", "start": 0, "count": count}
        if platform:
            search_input["orFilters"] = [
                {"and": [{"field": "platform", "values": [f"urn:li:dataPlatform:{platform}"]}]}
            ]
        data = await self.graphql(_SEARCH, {"input": search_input})
        return [summarize(r["entity"]) for r in data["searchAcrossEntities"]["searchResults"]]

    async def entity(self, urn: str) -> Optional[dict[str, Any]]:
        data = await self.graphql(_ENTITY, {"urn": urn})
        return summarize(data["entity"]) if data.get("entity") else None

    async def lineage(
        self, urn: str, direction: str, max_hops: int = 3, count: int = 50
    ) -> tuple[int, list[dict[str, Any]]]:
        degrees = ["1", "2", "3+"][: max(1, min(max_hops, 3))]
        data = await self.graphql(
            _LINEAGE,
            {
                "input": {
                    "urn": urn,
                    "direction": direction.upper(),
                    "query": "*",
                    "start": 0,
                    "count": count,
                    "orFilters": [{"and": [{"field": "degree", "values": degrees}]}],
                }
            },
        )
        result = data["searchAcrossLineage"]
        items = [
            {**summarize(r["entity"]), "degree": r.get("degree")} for r in result["searchResults"]
        ]
        return result["total"], items


async def create_access_token(ui_url: str, username: str, password: str) -> str:
    """Log in to the DataHub frontend and mint a personal access token for that user."""
    base = ui_url.rstrip("/")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            login = await client.post(
                f"{base}/logIn", json={"username": username, "password": password}
            )
        except httpx.HTTPError as e:
            raise DataHubError(f"Could not reach the DataHub UI at {base}: {e}") from e
        if login.status_code != 200:
            raise DataHubError(f"DataHub login failed ({login.status_code}). Check the credentials.")
        resp = await client.post(
            f"{base}/api/v2/graphql",
            json={
                "query": _CREATE_TOKEN,
                "variables": {
                    "input": {
                        "type": "PERSONAL",
                        "actorUrn": f"urn:li:corpuser:{username}",
                        "duration": "NO_EXPIRY",
                        "name": "datahub-ai-rca",
                        "description": "Created by the datahub-ai-rca workshop app",
                    }
                },
            },
        )
    body = resp.json() if resp.content else {}
    if resp.status_code != 200 or body.get("errors"):
        detail = (body.get("errors") or [{}])[0].get("message", resp.status_code)
        raise DataHubError(f"Could not create an access token: {detail}")
    return body["data"]["createAccessToken"]["accessToken"]
