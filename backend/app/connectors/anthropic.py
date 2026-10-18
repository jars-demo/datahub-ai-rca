import anthropic

from app.connectors.base import CheckResult, Connector, FieldSpec

DEFAULT_MODEL = "claude-opus-5-5"


class AnthropicConnector(Connector):
    id = "anthropic"
    name = "Claude"
    role = "Reasoning model"
    description = "Model used by the assistant and the analysis agent."
    docs_url = "https://console.anthropic.com/settings/keys"
    fields = [
        FieldSpec(
            key="api_key",
            label="API key",
            kind="secret",
            placeholder="sk-ant-…",
            help="Anthropic Console → API Keys.",
        ),
        FieldSpec(
            key="model",
            label="Model",
            default=DEFAULT_MODEL,
            placeholder=DEFAULT_MODEL,
        ),
    ]

    async def _test(self, values: dict[str, str]) -> CheckResult:
        model = values["model"]
        # Retrieving model metadata validates both the key and the model ID
        # without spending any tokens.
        async with anthropic.AsyncAnthropic(
            api_key=values["api_key"], timeout=15.0, max_retries=1
        ) as client:
            try:
                info = await client.models.retrieve(model)
            except anthropic.AuthenticationError:
                return CheckResult(ok=False, message="Anthropic rejected the API key.")
            except anthropic.PermissionDeniedError:
                return CheckResult(ok=False, message=f"This key can't access '{model}'.")
            except anthropic.NotFoundError:
                return CheckResult(ok=False, message=f"Model '{model}' was not found.")
            except anthropic.APIConnectionError:
                return CheckResult(ok=False, message="Could not reach the Anthropic API.")
            except anthropic.APIStatusError as e:
                return CheckResult(ok=False, message=f"Anthropic API error ({e.status_code}).")

        return CheckResult(
            ok=True,
            message=f"Connected. Using {info.display_name}.",
            details={"model": info.id},
        )
