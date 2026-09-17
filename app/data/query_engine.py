from __future__ import annotations

from typing import Any

import pandas as pd

from app.models import QueryResult, StructuredQuery


class QueryExecutionError(ValueError):
    """Raised for a controlled but unexecutable query."""


class QueryEngine:
    def __init__(self, dataframe: pd.DataFrame, max_list_rows: int = 100) -> None:
        self._df = dataframe.copy()
        self._max_list_rows = max_list_rows

    def apply_filters(self, query: StructuredQuery) -> pd.DataFrame:
        result = self._df
        for item in query.filters:
            field, op, value = item.field, item.operator, item.value
            series = result[field]
            if op == "eq":
                result = result[series == self._coerce(field, value)]
            elif op == "ne":
                result = result[series != self._coerce(field, value)]
            elif op == "in":
                result = result[series.isin([self._coerce(field, item) for item in value])]
            elif op in {"gt", "gte", "lt", "lte"}:
                compared = self._coerce(field, value)
                result = result[{"gt": series > compared, "gte": series >= compared, "lt": series < compared, "lte": series <= compared}[op]]
            elif op == "contains":
                result = result[series.str.contains(str(value), case=False, regex=False, na=False)]
            elif op == "not_resolved_within":
                hours = float(value)
                result = result[(result["status"] != "Resolved") | (result["resolution_time_hrs"] > hours)]
            else:  # pragma: no cover - Pydantic validates allowed operators
                raise QueryExecutionError("Unsupported filter operator")
        return result

    def execute(self, query: StructuredQuery) -> QueryResult:
        if query.operation == "anomalies":
            raise QueryExecutionError("Anomaly queries are handled by the anomaly service")
        filtered = self.apply_filters(query)
        if query.operation == "count":
            return QueryResult(result_type="scalar", value=int(len(filtered)))
        if query.operation == "average":
            numeric = pd.to_numeric(filtered[query.field], errors="coerce").dropna()
            return QueryResult(result_type="scalar", value=round(float(numeric.mean()), 2) if not numeric.empty else None)
        if query.operation == "percentage":
            if self._df.empty:
                return QueryResult(result_type="scalar", value=None)
            return QueryResult(result_type="scalar", value=round(len(filtered) / len(self._df) * 100, 2))
        if query.operation == "list":
            fields = query.select_fields or list(self._df.columns)
            limited = filtered.loc[:, fields].head(min(query.limit, self._max_list_rows))
            return QueryResult(result_type="table", rows=self._records(limited), total_rows=int(len(filtered)))
        if query.operation in {"group_by", "top"}:
            if query.metric == "count":
                grouped = filtered.groupby(query.group_field, dropna=False).size().reset_index(name="count")
                sort_column = "count"
            else:
                if query.field is None:
                    raise QueryExecutionError("average group query requires a numeric field")
                grouped = filtered.groupby(query.group_field, dropna=False)[query.field].mean().reset_index(name="average")
                sort_column = "average"
            grouped = grouped.sort_values(sort_column, ascending=query.sort == "asc").head(query.limit)
            return QueryResult(result_type="table", rows=self._records(grouped), total_rows=int(len(grouped)))
        raise QueryExecutionError("Unsupported operation")

    @staticmethod
    def _coerce(field: str, value: Any) -> Any:
        if field == "created_at":
            parsed = pd.to_datetime(value, errors="coerce")
            if pd.isna(parsed):
                raise QueryExecutionError("Invalid date filter")
            return parsed
        if field in {"response_time_hrs", "resolution_time_hrs", "customer_rating"}:
            try:
                return float(value)
            except (TypeError, ValueError) as exc:
                raise QueryExecutionError(f"Invalid numeric filter for {field}") from exc
        return value

    @staticmethod
    def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for row in frame.to_dict(orient="records"):
            output.append({key: (value.isoformat() if isinstance(value, pd.Timestamp) else None if pd.isna(value) else value) for key, value in row.items()})
        return output
