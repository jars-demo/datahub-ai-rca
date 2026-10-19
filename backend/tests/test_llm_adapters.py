"""The adapters translate one neutral conversation into each provider's wire format."""

from app.llm.anthropic_client import AnthropicClient
from app.llm.factory import build_llm
from app.llm.openai_client import OpenAICompatibleClient
from app.llm.types import LLMError, ToolCall, ToolResult, Turn

TURNS = [
    Turn(role="user", text="Why did quality drop?"),
    Turn(
        role="assistant",
        text="Checking scores.",
        tool_calls=[ToolCall(id="c1", name="quality_trend", arguments={"days": 7})],
    ),
    Turn(role="tool", tool_results=[ToolResult(call_id="c1", content='{"avg": 0.4}')]),
]


def test_openai_format_has_system_tool_calls_and_tool_messages() -> None:
    messages = OpenAICompatibleClient._messages("sys", TURNS)
    assert messages[0] == {"role": "system", "content": "sys"}
    call = messages[2]["tool_calls"][0]
    assert call["function"] == {"name": "quality_trend", "arguments": '{"days": 7}'}
    assert messages[3] == {"role": "tool", "tool_call_id": "c1", "content": '{"avg": 0.4}'}


def test_anthropic_format_uses_tool_use_and_tool_result_blocks() -> None:
    client = AnthropicClient(api_key="k", model="claude-opus-5-5")
    messages = client._messages(TURNS)
    assert messages[1]["content"][1] == {
        "type": "tool_use", "id": "c1", "name": "quality_trend", "input": {"days": 7}
    }
    assert messages[2]["role"] == "user"
    assert messages[2]["content"][0]["tool_use_id"] == "c1"


def test_anthropic_replays_its_own_raw_content_unchanged() -> None:
    raw = [{"type": "thinking", "thinking": "", "signature": "sig"}, {"type": "text", "text": "x"}]
    turn = Turn(role="assistant", text="x", raw=raw, raw_provider="anthropic")
    client = AnthropicClient(api_key="k", model="claude-opus-5-5")
    assert client._messages([turn])[0]["content"] is raw


def test_factory_picks_adapter_and_validates() -> None:
    assert isinstance(build_llm({"provider": "anthropic", "api_key": "k"}), AnthropicClient)
    groq = build_llm({"provider": "groq", "api_key": "k", "model": "some-model"})
    assert isinstance(groq, OpenAICompatibleClient)
    for bad in ({"provider": "groq", "api_key": "k"}, {"provider": "custom", "model": "m"}):
        try:
            build_llm(bad)
        except LLMError:
            continue
        raise AssertionError(f"expected LLMError for {bad}")
