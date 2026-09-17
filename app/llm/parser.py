from __future__ import annotations

import logging
import re
from typing import Any

from pydantic import ValidationError

from app.data.validator import ALLOWED_CATEGORIES, ALLOWED_PRIORITIES, ALLOWED_STATUSES
from app.llm.client import LLMClient, LLMUnavailableError
from app.llm.prompts import build_system_prompt
from app.models import StructuredQuery

logger = logging.getLogger(__name__)


class QueryParseError(ValueError):
    """A user question or model result cannot safely become a query."""


BLOCKED_PATTERNS = re.compile(
    r"ignore\s+((all\s+)?previous|your)\s+instructions|reveal\s+(the\s+)?system\s+prompt|"
    r"execute\s+python|drop\s+table|secret_key|environment\s+variables",
    re.IGNORECASE,
)


class StructuredQueryParser:
    def __init__(self, client: LLMClient) -> None:
        self._client = client

    def parse(self, question: str, reference_timestamp: str) -> StructuredQuery:
        if BLOCKED_PATTERNS.search(question):
            logger.warning("query_rejected reason=prompt_injection_pattern")
            raise QueryParseError("This request is unsupported for the ticket analytics system.")
        if re.search(r"\b(weather|news|stock price)\b", question, re.IGNORECASE):
            raise QueryParseError("This system answers questions about the support-ticket dataset only.")
        prompt = build_system_prompt(reference_timestamp)
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                attempt_prompt = prompt if attempt == 0 else (
                    prompt + "\nYour prior output was invalid. Return only one valid JSON object using "
                    "the supported operation and exact field names. Do not include explanation, Markdown, or extra keys."
                )
                raw = self._client.generate_structured_query(attempt_prompt, question)
                parsed = StructuredQuery.model_validate(raw)
                if parsed.operation == "unsupported":
                    raise QueryParseError("This question is unsupported or ambiguous. Please specify a ticket metric, field, or time range.")
                self._validate_filter_values(parsed)
                return parsed
            except LLMUnavailableError:
                raise
            except (ValidationError, QueryParseError, TypeError, ValueError) as exc:
                last_error = exc
                logger.warning("llm_output_rejected attempt=%s error_type=%s", attempt + 1, type(exc).__name__)
        raise QueryParseError("I could not safely interpret that question. Please ask using ticket fields or metrics.") from last_error

    @staticmethod
    def _validate_filter_values(query: StructuredQuery) -> None:
        enum_fields: dict[str, set[str]] = {
            "category": ALLOWED_CATEGORIES,
            "priority": ALLOWED_PRIORITIES,
            "status": ALLOWED_STATUSES,
        }
        for query_filter in query.filters:
            if query_filter.field not in enum_fields:
                continue
            values: list[Any] = query_filter.value if query_filter.operator == "in" else [query_filter.value]
            invalid = set(values).difference(enum_fields[query_filter.field])
            if invalid:
                raise QueryParseError(f"Unsupported value for {query_filter.field}")
