from __future__ import annotations

import pandas as pd

from app.data.loader import load_tickets
from app.data.query_engine import QueryEngine
from app.models import QueryFilter, StructuredQuery


def engine() -> tuple[pd.DataFrame, QueryEngine]:
    df = load_tickets(__import__("pathlib").Path("data/support_tickets.csv"))
    return df, QueryEngine(df)


def test_count_open_and_critical_unresolved() -> None:
    _, query_engine = engine()
    open_result = query_engine.execute(StructuredQuery(operation="count", filters=[QueryFilter(field="status", operator="eq", value="Open")]))
    critical_result = query_engine.execute(StructuredQuery(operation="count", filters=[QueryFilter(field="priority", operator="eq", value="Critical"), QueryFilter(field="status", operator="in", value=["Open", "Escalated"])]))
    assert open_result.value == 111
    assert critical_result.value == 31


def test_average_excludes_unresolved_null_ratings() -> None:
    _, query_engine = engine()
    result = query_engine.execute(StructuredQuery(operation="average", field="customer_rating", filters=[QueryFilter(field="category", operator="eq", value="Technical")]))
    assert result.value == 3.74


def test_group_and_date_filters_are_deterministic() -> None:
    _, query_engine = engine()
    query = StructuredQuery(operation="top", group_field="agent_id", filters=[QueryFilter(field="status", operator="eq", value="Resolved"), QueryFilter(field="created_at", operator="gte", value="2024-03-01"), QueryFilter(field="created_at", operator="lt", value="2024-04-01")], limit=1)
    result = query_engine.execute(query)
    assert result.rows == [{"agent_id": "AGT-01", "count": 16}]


def test_not_resolved_within_includes_null_resolution_times() -> None:
    _, query_engine = engine()
    query = StructuredQuery(operation="list", filters=[QueryFilter(field="priority", operator="eq", value="Critical"), QueryFilter(field="resolution_time_hrs", operator="not_resolved_within", value=12)], limit=100)
    result = query_engine.execute(query)
    assert result.total_rows == 34
    assert any(row["status"] != "Resolved" for row in result.rows or [])
