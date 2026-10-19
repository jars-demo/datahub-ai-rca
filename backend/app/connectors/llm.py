from app.connectors.base import CheckResult, Connector, FieldOption, FieldSpec
from app.llm.factory import build_llm
from app.llm.providers import DEFAULT_PROVIDER, PROVIDERS
from app.llm.types import LLMError

_MAX_LISTED = 8


class LLMConnector(Connector):
    id = "llm"
    name = "LLM provider"
    role = "Bring your own model"
    description = "Any provider: Anthropic, OpenAI, Gemini, Groq, OpenRouter, Mistral, Ollama and more."
    docs_url = "https://github.com/jars-demo/datahub-ai-rca#bring-your-own-model"
    fields = [
        FieldSpec(
            key="provider",
            label="Provider",
            kind="select",
            default=DEFAULT_PROVIDER,
            options=[FieldOption(value=p.id, label=p.label) for p in PROVIDERS.values()],
            env="LLM_PROVIDER",
        ),
        FieldSpec(
            key="model",
            label="Model",
            required=False,
            placeholder="Leave blank for the provider default",
            help="Anthropic defaults to claude-opus-5-5. Other providers: the test lists models.",
            env="LLM_MODEL",
        ),
        FieldSpec(
            key="api_key",
            label="API key",
            kind="secret",
            required=False,
            placeholder="Your provider API key",
            help="Not needed for Ollama.",
            env="LLM_API_KEY",
        ),
        FieldSpec(
            key="base_url",
            label="Base URL",
            kind="url",
            required=False,
            placeholder="Only for custom endpoints or self-hosted gateways",
            env="LLM_BASE_URL",
        ),
    ]

    def required_keys(self, values: dict[str, str]) -> set[str]:
        info = PROVIDERS.get(values.get("provider") or DEFAULT_PROVIDER)
        required = {"provider"}
        if info is None:
            return required
        if info.needs_key:
            required.add("api_key")
        if not info.default_model:
            required.add("model")
        if info.adapter == "openai" and not info.base_url:
            required.add("base_url")
        return required

    async def _test(self, values: dict[str, str]) -> CheckResult:
        try:
            client = build_llm(values)
            models = await client.list_models()
        except LLMError as e:
            return CheckResult(ok=False, message=str(e))

        info = PROVIDERS[values.get("provider") or DEFAULT_PROVIDER]
        details = {"provider": info.label, "model": client.model}
        # Some gateways don't list every model they serve, so only fail when the list
        # clearly comes from the provider and the model is absent.
        if models and client.model not in models:
            close = [m for m in models if client.model.split("/")[-1][:6] in m][:_MAX_LISTED]
            return CheckResult(
                ok=False,
                message=f"Connected to {info.label}, but model '{client.model}' isn't available.",
                details={**details, "available": close or models[:_MAX_LISTED]},
            )
        return CheckResult(
            ok=True, message=f"Connected to {info.label} · {client.model}.", details=details
        )
