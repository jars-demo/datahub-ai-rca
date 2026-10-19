import asyncio
from typing import Optional

from app.agent import runner
from app.llm.types import Completion, LLMClient, ToolCall, ToolSpec, Turn
from app.seed import traffic


class ScriptedLLM(LLMClient):
    """Calls one tool, then answers using the tool result it was given."""

    provider = "scripted"
    model = "scripted-1"

    async def complete(
        self, system: str, turns: list[Turn], tools: Optional[list[ToolSpec]] = None, max_tokens: int = 0
    ) -> Completion:
        if turns[-1].role == "user":
            call = ToolCall(id="t1", name="quality_trend", arguments={"score_name": "correctness"})
            return Completion(text="", tool_calls=[call], stop_reason="tool_use", model=self.model)
        result = turns[-1].tool_results[0]
        return Completion(text=f"answer from {result.content[:20]}", tool_calls=[], stop_reason="end", model=self.model)

    async def list_models(self) -> list[str]:
        return [self.model]


def test_agent_loop_runs_tools_and_returns_answer(monkeypatch) -> None:
    async def fake_trend(ctx, args):
        return {"daily": [{"avg": 0.9}]}

    spec, _ = runner.TOOLS["quality_trend"]
    monkeypatch.setitem(runner.TOOLS, "quality_trend", (spec, fake_trend))

    async def collect():
        return [e async for e in runner.investigate("why?", ScriptedLLM(), ctx=None)]

    events = asyncio.run(collect())
    types = [e["type"] for e in events]
    assert types == ["start", "tool_call", "tool_result", "answer", "done"]
    assert events[2]["ok"] and events[2]["summary"] == "1 daily"
    assert events[3]["markdown"].startswith("answer from")


def test_unknown_tool_is_reported_back_as_error() -> None:
    result, data = asyncio.run(runner._execute(None, ToolCall(id="x", name="nope", arguments={})))
    assert result.is_error and data is None


def test_seed_traffic_shows_regression_on_v3_only() -> None:
    traces = traffic.generate()
    v2 = [t.scores["correctness"] for t in traces if t.prompt_version == 2]
    v3 = [t.scores["correctness"] for t in traces if t.prompt_version == 3]
    assert v2 and v3
    assert sum(v2) / len(v2) > 0.8
    assert sum(v3) / len(v3) < sum(v2) / len(v2) - 0.3
    assert {t.namespace for t in traces if t.prompt_version == 3} == {"help-center-2023-archive"}


def test_seed_is_deterministic_and_event_ids_stable() -> None:
    a = traffic.to_events(traffic.generate(), "m")
    b = traffic.to_events(traffic.generate(), "m")
    assert [e["id"] for e in a] == [e["id"] for e in b]
    assert len({e["id"] for e in a}) == len(a)
