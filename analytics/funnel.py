"""Course completion funnel and drop-off analytics."""

from __future__ import annotations
import pandas as pd

FUNNEL_STAGES = (
    ("enrolled", 0),
    ("started", 1),
    ("25_percent", 25),
    ("50_percent", 50),
    ("75_percent", 75),
    ("completed", 100),
)


def build_completion_funnel(df: pd.DataFrame) -> pd.DataFrame:
    """Build cumulative funnel counts and stage conversion/drop-off rates."""
    required = {"student_id", "course_id", "completion_pct"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    columns = ["stage", "student_count", "conversion_rate", "dropoff_rate"]
    if df.empty:
        return pd.DataFrame(columns=columns)

    data = df[["student_id", "course_id", "completion_pct"]].copy()
    data["completion_pct"] = pd.to_numeric(data["completion_pct"], errors="coerce")
    data = data.dropna(subset=["student_id", "course_id", "completion_pct"])
    data["completion_pct"] = data["completion_pct"].clip(0, 100)
    data = data.drop_duplicates(["student_id", "course_id"])

    enrolled = len(data)
    if enrolled == 0:
        return pd.DataFrame(columns=columns)

    rows = []
    previous_count = enrolled

    for stage, threshold in FUNNEL_STAGES:
        count = enrolled if stage == "enrolled" else int(
            (data["completion_pct"] >= threshold).sum()
        )
        conversion = round(count / enrolled * 100, 2)
        dropoff = (
            round((previous_count - count) / previous_count * 100, 2)
            if previous_count else 0.0
        )
        rows.append({
            "stage": stage,
            "student_count": count,
            "conversion_rate": conversion,
            "dropoff_rate": dropoff,
        })
        previous_count = count

    return pd.DataFrame(rows, columns=columns)