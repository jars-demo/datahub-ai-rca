import httpx

from app.connectors.base import CheckResult, Connector, DetailValue, FieldSpec

_WHOAMI = "{ me { corpUser { username } } }"


class DataHubConnector(Connector):
    id = "datahub"
    name = "DataHub"
    role = "Metadata graph"
    description = "Lineage, ownership and change history across systems."
    docs_url = "https://docs.datahub.com/docs/authentication/personal-access-tokens"
    fields = [
        FieldSpec(
            key="gms_url",
            label="GMS URL",
            kind="url",
            default="http://localhost:8080",
            placeholder="http://localhost:8080",
            help="The DataHub metadata service, not the UI (port 9002).",
        ),
        FieldSpec(
            key="token",
            label="Personal access token",
            kind="secret",
            placeholder="eyJhbGciOi…",
            help="DataHub UI → Settings → Access Tokens.",
        ),
    ]

    async def _test(self, values: dict[str, str]) -> CheckResult:
        base = values["gms_url"].rstrip("/")
        headers = {"Authorization": f"Bearer {values['token']}"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                config = await client.get(f"{base}/config")
                whoami = await client.post(
                    f"{base}/api/graphql", json={"query": _WHOAMI}, headers=headers
                )
        except httpx.HTTPError as e:
            return CheckResult(ok=False, message=f"Could not reach {base}: {e}")

        if config.status_code != 200:
            return CheckResult(
                ok=False, message=f"{base} doesn't look like DataHub GMS ({config.status_code})."
            )
        version = (
            config.json().get("versions", {}).get("acryldata/datahub", {}).get("version", "unknown")
        )
        details: dict[str, DetailValue] = {"version": version}

        if whoami.status_code in (401, 403):
            return CheckResult(
                ok=False,
                message="DataHub is reachable, but the token was rejected.",
                details=details,
            )
        if whoami.status_code != 200:
            return CheckResult(
                ok=False, message=f"GraphQL error ({whoami.status_code}).", details=details
            )

        user = ((whoami.json().get("data") or {}).get("me") or {}).get("corpUser") or {}
        details["user"] = user.get("username", "unknown")
        return CheckResult(
            ok=True,
            message=f"Connected to DataHub {version} as {details['user']}.",
            details=details,
        )
