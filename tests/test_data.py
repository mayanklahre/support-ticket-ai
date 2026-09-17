from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.data.loader import load_tickets
from app.data.validator import DatasetValidationError, REQUIRED_COLUMNS, validate_dataframe


def test_csv_loads_with_real_schema() -> None:
    df = load_tickets(Path("data/support_tickets.csv"))
    assert len(df) == 500
    assert set(df.columns) == REQUIRED_COLUMNS
    assert pd.api.types.is_datetime64_any_dtype(df["created_at"])
    assert df["ticket_id"].is_unique


def test_legitimate_unresolved_nulls_are_preserved() -> None:
    df = load_tickets(Path("data/support_tickets.csv"))
    unresolved = df["status"].isin(["Open", "Escalated"])
    assert df.loc[unresolved, "resolution_time_hrs"].isna().all()
    assert df.loc[unresolved, "customer_rating"].isna().all()


def test_invalid_enum_is_rejected() -> None:
    df = load_tickets(Path("data/support_tickets.csv"))
    df.loc[0, "status"] = "Unknown"
    with pytest.raises(DatasetValidationError):
        validate_dataframe(df)
