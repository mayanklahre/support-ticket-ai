from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = {
    "ticket_id", "created_at", "category", "priority", "status",
    "response_time_hrs", "resolution_time_hrs", "agent_id", "customer_rating", "issue_summary",
}
ALLOWED_CATEGORIES = {"Billing", "Technical", "General"}
ALLOWED_PRIORITIES = {"Low", "Medium", "High", "Critical"}
ALLOWED_STATUSES = {"Open", "Resolved", "Escalated"}


class DatasetValidationError(ValueError):
    """Raised when the input dataset violates the assessment schema."""


def validate_dataframe(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise DatasetValidationError(f"Missing required columns: {sorted(missing)}")
    if df.empty:
        raise DatasetValidationError("Dataset must contain at least one ticket")
    if df["ticket_id"].isna().any() or df["ticket_id"].duplicated().any():
        raise DatasetValidationError("ticket_id values must be present and unique")
    if df["created_at"].isna().any():
        raise DatasetValidationError("created_at contains invalid or missing timestamps")
    for column, allowed in {
        "category": ALLOWED_CATEGORIES,
        "priority": ALLOWED_PRIORITIES,
        "status": ALLOWED_STATUSES,
    }.items():
        invalid = set(df[column].dropna().unique()).difference(allowed)
        if invalid or df[column].isna().any():
            raise DatasetValidationError(f"{column} contains invalid values: {sorted(invalid)}")
    for column in ("response_time_hrs", "resolution_time_hrs", "customer_rating"):
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise DatasetValidationError(f"{column} must be numeric")
    if (df["response_time_hrs"] < 0).any() or (df["resolution_time_hrs"].dropna() < 0).any():
        raise DatasetValidationError("time values must be non-negative")
    ratings = df["customer_rating"].dropna()
    if not ratings.between(1, 5).all():
        raise DatasetValidationError("customer_rating must be within 1 to 5")
    unresolved = df["status"].isin(["Open", "Escalated"])
    if df.loc[unresolved, "resolution_time_hrs"].notna().any() or df.loc[unresolved, "customer_rating"].notna().any():
        raise DatasetValidationError("unresolved tickets must have null resolution_time_hrs and customer_rating")
