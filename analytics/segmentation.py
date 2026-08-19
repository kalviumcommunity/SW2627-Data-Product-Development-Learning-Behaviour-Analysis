"""Rule-based learner behaviour.

The segmentation layer converts the existing student-course behavioural
features into deterministic, explainable learner segments.

Expected input columns:
- student_id
- course_id
- total_study_hours
- avg_session_length
- quiz_accuracy
- quiz_frequency
- active_days
- learning_streak
- days_since_last_activity
- weekly_sessions
- completion_pct
- status
"""

from __future__ import annotations

import pandas as pd


SEGMENT_LABELS = (
    "completed",
    "high_engagement",
    "struggling_learner",
    "at_risk",
    "low_engagement",
    "consistent_learner",
)


def _require_columns(df: pd.DataFrame) -> None:
    required = {
        "student_id",
        "course_id",
        "total_study_hours",
        "quiz_accuracy",
        "active_days",
        "learning_streak",
        "days_since_last_activity",
        "weekly_sessions",
        "completion_pct",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def _segment_row(row: pd.Series) -> str:
    """Assign one deterministic behaviour segment to a learner."""
    completion = float(row["completion_pct"])
    quiz_accuracy = float(row["quiz_accuracy"])
    active_days = float(row["active_days"])
    streak = float(row["learning_streak"])
    inactivity = float(row["days_since_last_activity"])
    weekly_sessions = float(row["weekly_sessions"])
    study_hours = float(row["total_study_hours"])

    if completion >= 100:
        return "completed"

    if inactivity >= 14 or (
        active_days <= 2 and weekly_sessions < 1
    ):
        return "at_risk"

    if (
        study_hours >= 5
        and quiz_accuracy >= 75
        and active_days >= 5
    ):
        return "high_engagement"

    if quiz_accuracy < 50 and (active_days >= 2 or weekly_sessions >= 1):
        return "struggling_learner"

    if active_days <= 2 or weekly_sessions < 1:
        return "low_engagement"

    if streak >= 3 or weekly_sessions >= 2:
        return "consistent_learner"

    return "low_engagement"


def segment_learners(df: pd.DataFrame) -> pd.DataFrame:
    """Return student-course records with an explainable behaviour segment."""
    _require_columns(df)

    output = df.copy()

    numeric_columns = [
        "total_study_hours",
        "quiz_accuracy",
        "active_days",
        "learning_streak",
        "days_since_last_activity",
        "weekly_sessions",
        "completion_pct",
    ]

    for column in numeric_columns:
        output[column] = pd.to_numeric(
            output[column], errors="coerce"
        )

    if output.empty:
        output["segment"] = pd.Series(dtype="object")
        return output[["student_id", "course_id", "segment"]]

    if output[numeric_columns].isna().any().any():
        raise ValueError("Behavioural feature columns contain invalid numeric values")

    output["segment"] = output.apply(_segment_row, axis=1)

    return output[["student_id", "course_id", "segment"]].reset_index(drop=True)


def segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return segment counts and percentages."""
    segmented = segment_learners(df)

    if segmented.empty:
        return pd.DataFrame(
            columns=["segment", "student_count", "percentage"]
        )

    summary = (
        segmented.groupby("segment", as_index=False)
        .size()
        .rename(columns={"size": "student_count"})
    )

    total = summary["student_count"].sum()
    summary["percentage"] = (
        summary["student_count"] / total * 100
    ).round(2)

    return summary.sort_values(
        ["student_count", "segment"],
        ascending=[False, True],
    ).reset_index(drop=True)
