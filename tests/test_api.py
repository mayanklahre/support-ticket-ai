from __future__ import annotations

from fastapi.testclient import TestClient

from app.llm.client import LLMUnavailableError
from app.main import create_app
from tests.conftest import FakeLLM


def test_health_query_and_anomalies(settings) -> None:
    app = create_app(settings, FakeLLM())
    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["record_count"] == 500
    assert health.json()["status_counts"]["Open"] == 111
    answer = client.post("/query", json={"question": "How many tickets are currently open?"})
    assert answer.status_code == 200
    assert answer.json()["result"]["value"] == 111
    anomalies = client.get("/anomalies?type=statistical")
    assert anomalies.status_code == 200
    assert anomalies.json()["summary"]["total"] == 21


def test_invalid_payload_and_empty_question(settings) -> None:
    client = TestClient(create_app(settings, FakeLLM()))
    assert client.post("/query", json={}).status_code == 422
    assert client.post("/query", json={"question": "   "}).status_code == 422


class DownLLM(FakeLLM):
    def generate_structured_query(self, system_prompt: str, question: str) -> dict:
        raise LLMUnavailableError("down")


def test_llm_unavailable_returns_503_but_health_is_healthy(settings) -> None:
    client = TestClient(create_app(settings, DownLLM(available=False)))
    assert client.get("/health").json()["llm_status"] == "unavailable"
    assert client.post("/query", json={"question": "How many tickets are open?"}).status_code == 503
