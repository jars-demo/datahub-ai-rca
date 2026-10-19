import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@lru_cache
def scenario() -> dict[str, Any]:
    return json.loads((DATA_DIR / "scenario.json").read_text())


@lru_cache
def prompt_versions() -> list[dict[str, Any]]:
    return json.loads((DATA_DIR / "langfuse" / "prompts.json").read_text())
