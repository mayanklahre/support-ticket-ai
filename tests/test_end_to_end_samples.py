from __future__ import annotations

from pathlib import Path

from app.anomalies.detector import AnomalyDetector
from app.data.loader import load_tickets
from app.data.query_engine import QueryEngine
from app.llm.parser import StructuredQueryParser
from app.services.query_service import QueryService
from tests.conftest import FakeLLM


def test_all_assessment_sample_intents_compute_ground_truth() -> None:
    df = load_tickets(Path("data/support_tickets.csv"))
    detector = AnomalyDetector(df)
    responses = [
        {"operation": "count", "filters": [{"field": "status", "operator": "eq", "value": "Open"}]},
        {"operation": "top", "group_field": "agent_id", "filters": [{"field": "status", "operator": "eq", "value": "Resolved"}, {"field": "created_at", "operator": "gte", "value": "2024-03-01"}, {"field": "created_at", "operator": "lt", "value": "2024-04-01"}], "limit": 1},
        {"operation": "list", "filters": [{"field": "priority", "operator": "eq", "value": "Critical"}, {"field": "resolution_time_hrs", "operator": "not_resolved_within", "value": 12}], "limit": 100},
        {"operation": "average", "field": "customer_rating", "filters": [{"field": "category", "operator": "eq", "value": "Technical"}]},
        {"operation": "anomalies", "anomaly_type": "statistical", "filters": [{"field": "created_at", "operator": "gte", "value": "2024-03-25"}, {"field": "created_at", "operator": "lt", "value": "2024-04-01"}]},
    ]

    class SequentialLLM(FakeLLM):
        def generate_structured_query(self, system_prompt: str, question: str) -> dict:
            return responses.pop(0)

    service = QueryService(QueryEngine(df), StructuredQueryParser(SequentialLLM()), detector, detector.reference_timestamp)
    results = [service.answer(question).result for question in [
        "How many tickets are currently open?",
        "Which agent resolved the most tickets this month?",
        "Show me all Critical tickets not resolved within 12 hours.",
        "What is the average customer rating for Technical category tickets?",
        "Are there any anomalies in resolution times this week?",
    ]]
    assert results[0].value == 111
    assert results[1].rows == [{"agent_id": "AGT-01", "count": 16}]
    assert results[2].total_rows == 34
    assert results[3].value == 3.74
    assert results[4].total_rows == 5
