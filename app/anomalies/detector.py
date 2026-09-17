from __future__ import annotations

import pandas as pd

from app.models import AnomalyItem, AnomalyResponse


class AnomalyDetector:
    def __init__(self, dataframe: pd.DataFrame) -> None:
        self._df = dataframe.copy()
        self.reference_timestamp = self._df["created_at"].max()

    def detect(self, anomaly_type: str = "all", start: pd.Timestamp | None = None, end: pd.Timestamp | None = None) -> AnomalyResponse:
        if anomaly_type not in {"all", "business", "statistical"}:
            raise ValueError("type must be one of all, business, statistical")
        business = self._business()
        statistical, upper_bound = self._statistical()
        selected: list[AnomalyItem] = []
        if anomaly_type in {"all", "business"}:
            selected.extend(business)
        if anomaly_type in {"all", "statistical"}:
            selected.extend(statistical)
        if start is not None:
            selected = [item for item in selected if pd.Timestamp(item.created_at) >= start]
        if end is not None:
            selected = [item for item in selected if pd.Timestamp(item.created_at) < end]
        selected.sort(key=lambda item: (item.created_at, item.ticket_id), reverse=True)
        selected_business = sum(item.type == "business" for item in selected)
        selected_statistical = sum(item.type == "statistical" for item in selected)
        return AnomalyResponse(
            summary={"total": len(selected), "business_rule": selected_business,
                     "statistical": selected_statistical,
                     "resolution_iqr_upper_bound_hours": round(upper_bound, 2)},
            anomalies=selected,
        )

    def _business(self) -> list[AnomalyItem]:
        frame = self._df[
            self._df["priority"].isin(["High", "Critical"])
            & self._df["status"].isin(["Open", "Escalated"])
        ].copy()
        frame["age_hours"] = (self.reference_timestamp - frame["created_at"]).dt.total_seconds() / 3600
        frame = frame[frame["age_hours"] > 24]
        return [AnomalyItem(ticket_id=row.ticket_id, type="business", reason="Unresolved High or Critical ticket is older than 24 hours relative to the dataset reference timestamp.", created_at=row.created_at.isoformat(), priority=row.priority, status=row.status, age_hours=round(float(row.age_hours), 2)) for row in frame.itertuples()]

    def _statistical(self) -> tuple[list[AnomalyItem], float]:
        resolved = self._df.loc[self._df["status"] == "Resolved", "resolution_time_hrs"].dropna()
        q1, q3 = resolved.quantile(0.25), resolved.quantile(0.75)
        upper_bound = float(q3 + 1.5 * (q3 - q1))
        frame = self._df[(self._df["status"] == "Resolved") & (self._df["resolution_time_hrs"] > upper_bound)]
        reason = "Resolution time exceeds the statistical upper bound defined by Q3 + 1.5 × IQR."
        items = [AnomalyItem(ticket_id=row.ticket_id, type="statistical", reason=reason, created_at=row.created_at.isoformat(), priority=row.priority, status=row.status, resolution_time_hrs=round(float(row.resolution_time_hrs), 2)) for row in frame.itertuples()]
        return items, upper_bound
