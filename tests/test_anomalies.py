from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from app.anomalies.detector import AnomalyDetector
from app.data.loader import load_tickets


def test_business_and_statistical_anomalies_match_ground_truth() -> None:
    detector = AnomalyDetector(load_tickets(Path("data/support_tickets.csv")))
    result = detector.detect()
    assert result.summary["business_rule"] == 80
    assert result.summary["statistical"] == 21
    assert result.summary["total"] == 101


def test_statistical_anomalies_use_resolved_tickets_only() -> None:
    detector = AnomalyDetector(load_tickets(Path("data/support_tickets.csv")))
    result = detector.detect("statistical")
    assert all(item.status == "Resolved" and item.resolution_time_hrs is not None for item in result.anomalies)
    assert result.summary["resolution_iqr_upper_bound_hours"] == 48.15


def test_this_week_statistical_anomalies() -> None:
    detector = AnomalyDetector(load_tickets(Path("data/support_tickets.csv")))
    start = detector.reference_timestamp.normalize() - timedelta(days=int(detector.reference_timestamp.weekday()))
    result = detector.detect("statistical", start, start + timedelta(days=7))
    assert result.summary["total"] == 5
    assert {item.ticket_id for item in result.anomalies} == {"TKT-108", "TKT-130", "TKT-158", "TKT-255", "TKT-400"}
