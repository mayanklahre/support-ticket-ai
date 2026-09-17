from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


FieldName = Literal[
    "ticket_id", "created_at", "category", "priority", "status",
    "response_time_hrs", "resolution_time_hrs", "agent_id",
    "customer_rating", "issue_summary",
]
Operation = Literal["count", "list", "average", "group_by", "top", "percentage", "anomalies", "unsupported"]
Operator = Literal["eq", "ne", "in", "gt", "gte", "lt", "lte", "contains", "not_resolved_within"]


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=500)

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question must not be empty")
        return value


class QueryFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: FieldName
    operator: Operator
    value: Any

    @model_validator(mode="after")
    def validate_operator(self) -> "QueryFilter":
        if self.operator == "in" and not isinstance(self.value, list):
            raise ValueError("the 'in' operator requires a list value")
        if self.operator == "contains" and self.field != "issue_summary":
            raise ValueError("contains is only supported for issue_summary")
        if self.operator == "not_resolved_within" and self.field != "resolution_time_hrs":
            raise ValueError("not_resolved_within only applies to resolution_time_hrs")
        return self


class StructuredQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation: Operation
    field: FieldName | None = None
    group_field: FieldName | None = None
    metric: Literal["count", "average"] = "count"
    filters: list[QueryFilter] = Field(default_factory=list)
    sort: Literal["asc", "desc"] = "desc"
    # Returning the full bounded result is the safer default for explicit list requests.
    # QueryEngine and configuration still cap every list at 100 rows.
    limit: int = Field(default=100, ge=1, le=100)
    select_fields: list[FieldName] | None = None
    anomaly_type: Literal["all", "business", "statistical"] = "all"

    @model_validator(mode="after")
    def validate_shape(self) -> "StructuredQuery":
        if self.operation in {"average", "percentage"} and self.field is None:
            raise ValueError(f"{self.operation} requires a field")
        if self.operation in {"group_by", "top"} and self.group_field is None:
            raise ValueError(f"{self.operation} requires group_field")
        if self.operation == "average" and self.field not in {
            "response_time_hrs", "resolution_time_hrs", "customer_rating"
        }:
            raise ValueError("average supports numeric fields only")
        return self


class QueryResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    result_type: Literal["scalar", "table"]
    value: float | int | None = None
    rows: list[dict[str, Any]] | None = None
    total_rows: int | None = None


class QueryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str
    parsed_query: StructuredQuery
    result: QueryResult
    explanation: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["healthy"]
    record_count: int
    llm_provider: str
    llm_status: Literal["available", "unavailable"]
    dataset_reference_date: str
    status_counts: dict[str, int] = Field(default_factory=dict)


class AnomalyItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticket_id: str
    type: Literal["business", "statistical"]
    reason: str
    created_at: str
    priority: str
    status: str
    resolution_time_hrs: float | None = None
    age_hours: float | None = None


class AnomalyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: dict[str, int | float]
    anomalies: list[AnomalyItem]
