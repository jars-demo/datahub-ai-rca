import httpx

from app.connectors.base import CheckResult, Connector, FieldSpec


class LangfuseConnector(Connector):
    id = "langfuse"
    name = "Langfuse"
    role = "LLM observability"
    description = "Traces, prompt versions and evaluation scores."
    docs_url = "https://langfuse.com/faq/all/where-are-langfuse-api-keys"
    fields = [
        FieldSpec(
            key="host",
            label="Host",
            kind="url",
            default="https://cloud.langfuse.com",
            placeholder="https://cloud.langfuse.com",
            help="Use https://us.cloud.langfuse.com for the US region, or your self-hosted URL.",
            env="LANGFUSE_HOST",
        ),
        FieldSpec(
            key="public_key",
            label="Public key",
            placeholder="pk-lf-…",
            help="Langfuse project → Settings → API Keys.",
            env="LANGFUSE_PUBLIC_KEY",
        ),
        FieldSpec(
            key="secret_key",
            label="Secret key",
            kind="secret",
            placeholder="sk-lf-…",
            env="LANGFUSE_SECRET_KEY",
        ),
    ]

    async def _test(self, values: dict[str, str]) -> CheckResult:
        host = values["host"].rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Langfuse keys are project-scoped; this returns the key's project.
                resp = await client.get(
                    f"{host}/api/public/projects",
                    auth=(values["public_key"], values["secret_key"]),
                )
        except httpx.HTTPError as e:
            return CheckResult(ok=False, message=f"Could not reach {host}: {e}")

        if resp.status_code in (401, 403):
            return CheckResult(ok=False, message="Langfuse rejected the key pair.")
        if resp.status_code != 200:
            return CheckResult(
                ok=False, message=f"Unexpected response from Langfuse ({resp.status_code})."
            )

        projects = resp.json().get("data", [])
        names = [p.get("name", p.get("id", "?")) for p in projects]
        label = names[0] if names else "unknown project"
        return CheckResult(
            ok=True,
            message=f"Connected to project '{label}'.",
            details={"projects": names, "host": host},
        )
