from app.connectors.base import CheckResult, Connector, DetailValue, FieldSpec
from app.services.datahub_api import DataHubAPI, DataHubError

_WHOAMI = "query whoami { me { corpUser { username } } }"


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
            help="The DataHub metadata service (GMS), not the UI.",
            env="DATAHUB_GMS_URL",
        ),
        FieldSpec(
            key="ui_url",
            label="UI URL",
            kind="url",
            default="http://localhost:9002",
            placeholder="http://localhost:9002",
            help="Used for links into DataHub and to create a token with your login.",
            env="DATAHUB_UI_URL",
        ),
        FieldSpec(
            key="token",
            label="Personal access token",
            kind="secret",
            placeholder="eyJhbGciOi…",
            help="DataHub → Settings → Access Tokens, or use “Create token” below.",
            env="DATAHUB_TOKEN",
        ),
    ]

    async def _test(self, values: dict[str, str]) -> CheckResult:
        api = DataHubAPI(values["gms_url"], values["token"], values.get("ui_url", ""))
        try:
            config = await api.server_config()
        except DataHubError as e:
            return CheckResult(ok=False, message=str(e))
        version_info = config.get("versions", {}).get("acryldata/datahub", {})
        details: dict[str, DetailValue] = {
            "version": version_info.get("version", "unknown"),
            "commit": str(version_info.get("commit", ""))[:10],
        }
        try:
            data = await api.graphql(_WHOAMI, {})
        except DataHubError as e:
            return CheckResult(ok=False, message=f"DataHub is reachable, but: {e}", details=details)
        user = ((data.get("me") or {}).get("corpUser") or {}).get("username", "unknown")
        details["user"] = user
        return CheckResult(
            ok=True,
            message=f"Connected to DataHub {details['version']} as {user}.",
            details=details,
        )
