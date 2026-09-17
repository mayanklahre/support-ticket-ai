from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.llm.client import LLMClient


class FakeLLM(LLMClient):
    def __init__(self, response: dict | None = None, available: bool = True) -> None:
        self.response = response or {"operation": "count", "filters": [{"field": "status", "operator": "eq", "value": "Open"}]}
        self.available = available
        self.calls = 0

    def generate_structured_query(self, system_prompt: str, question: str) -> dict:
        self.calls += 1
        return self.response

    def is_available(self) -> bool:
        return self.available


@pytest.fixture
def settings() -> Settings:
    return Settings(data_path=Path("data/support_tickets.csv"), llm_provider="ollama", max_list_rows=100)
