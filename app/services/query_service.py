from __future__ import annotations

import logging

import pandas as pd

from app.anomalies.detector import AnomalyDetector
from app.data.query_engine import QueryEngine
from app.llm.parser import StructuredQueryParser
from app.models import QueryResponse, QueryResult, StructuredQuery

logger = logging.getLogger(__name__)


class QueryService:
    def __init__(self, engine: QueryEngine, parser: StructuredQueryParser, detector: AnomalyDetector, reference_timestamp: pd.Timestamp) -> None:
        self._engine = engine
        self._parser = parser
        self._detector = detector
        self._reference_timestamp = reference_timestamp

    def answer(self, question: str) -> QueryResponse:
        parsed = self._parser.parse(question, self._reference_timestamp.isoformat())
        if parsed.operation == "anomalies":
            start, end = self._relative_week_bounds(parsed)
            anomaly_result = self._detector.detect(parsed.anomaly_type, start, end)
            result = QueryResult(result_type="table", rows=[item.model_dump() for item in anomaly_result.anomalies], total_rows=len(anomaly_result.anomalies))
            explanation = f"Found {len(anomaly_result.anomalies)} {parsed.anomaly_type} anomaly records."
        else:
            result = self._engine.execute(parsed)
            explanation = self._explain(parsed, result)
        logger.info("query_executed operation=%s", parsed.operation)
        return QueryResponse(question=question, parsed_query=parsed, result=result, explanation=explanation,
                             metadata={"dataset_reference_timestamp": self._reference_timestamp.isoformat()})

    def _relative_week_bounds(self, parsed: StructuredQuery) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
        # The parser encodes "this week" as deterministic bounds; retain a safe default for anomaly questions.
        dates = {f.operator: f.value for f in parsed.filters if f.field == "created_at"}
        if "gte" in dates and "lt" in dates:
            return pd.Timestamp(dates["gte"]), pd.Timestamp(dates["lt"])
        week_start = self._reference_timestamp.normalize() - pd.Timedelta(days=self._reference_timestamp.weekday())
        return week_start, week_start + pd.Timedelta(days=7)

    @staticmethod
    def _explain(query: StructuredQuery, result: QueryResult) -> str:
        if result.result_type == "scalar":
            if query.operation == "count":
                return f"The exact count is {result.value}."
            if query.operation == "percentage":
                return f"The exact percentage is {result.value}%."
            return f"The average is {result.value}. Null values were excluded."
        if query.operation == "list":
            return f"Returned {len(result.rows or [])} of {result.total_rows or 0} matching tickets."
        return f"Returned {len(result.rows or [])} grouped results."
