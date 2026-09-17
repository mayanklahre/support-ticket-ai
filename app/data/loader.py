from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from app.data.validator import DatasetValidationError, validate_dataframe

logger = logging.getLogger(__name__)


def load_tickets(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise DatasetValidationError(f"Dataset not found: {path}")
    try:
        df = pd.read_csv(path, encoding="utf-8")
    except (OSError, UnicodeDecodeError, pd.errors.ParserError) as exc:
        raise DatasetValidationError("Unable to read support ticket CSV") from exc
    df["created_at"] = pd.to_datetime(df["created_at"], format="%Y-%m-%d %H:%M", errors="coerce")
    for column in ("response_time_hrs", "resolution_time_hrs", "customer_rating"):
        df[column] = pd.to_numeric(df[column], errors="coerce")
    validate_dataframe(df)
    logger.info("dataset_loaded record_count=%s", len(df))
    return df


def dataset_metadata(df: pd.DataFrame) -> dict[str, object]:
    return {
        "record_count": int(len(df)),
        "min_created_at": df["created_at"].min().isoformat(),
        "max_created_at": df["created_at"].max().isoformat(),
        "categories": sorted(df["category"].unique().tolist()),
        "priorities": sorted(df["priority"].unique().tolist()),
        "statuses": sorted(df["status"].unique().tolist()),
        "agent_count": int(df["agent_id"].nunique()),
    }
