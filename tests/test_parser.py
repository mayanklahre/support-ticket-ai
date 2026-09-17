from __future__ import annotations

from app.llm.parser import StructuredQueryParser
from tests.conftest import FakeLLM


def test_parser_accepts_valid_mocked_structured_query() -> None:
    response = {"operation": "top", "group_field": "agent_id", "filters": [{"field": "status", "operator": "eq", "value": "Resolved"}], "limit": 1}
    parsed = StructuredQueryParser(FakeLLM(response)).parse("Which agent resolved the most?", "2024-03-30T18:06:00")
    assert parsed.operation == "top"
    assert parsed.group_field == "agent_id"


def test_parser_retries_once_after_malformed_output() -> None:
    class RetryLLM(FakeLLM):
        def generate_structured_query(self, system_prompt: str, question: str) -> dict:
            self.calls += 1
            return {"operation": "execute_python"} if self.calls == 1 else {"operation": "count", "filters": []}
    client = RetryLLM()
    assert StructuredQueryParser(client).parse("How many tickets?", "2024-03-30T18:06:00").operation == "count"
    assert client.calls == 2


def test_parser_returns_controlled_error_for_ambiguous_model_intent() -> None:
    import pytest
    from app.llm.parser import QueryParseError
    with pytest.raises(QueryParseError):
        StructuredQueryParser(FakeLLM({"operation": "unsupported"})).parse("Show me the worst tickets", "2024-03-30T18:06:00")
