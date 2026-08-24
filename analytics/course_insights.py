"""Course-level learner analytics built on the canonical insight table."""

from __future__ import annotations

import pandas as pd

from analytics.learner_insights import build_learner_insights


REQUIRED_COLUMNS = {
    "student_id",
    "course_id",
    "status",
    "completion_pct",
    "total_study_hours",
    "avg_session_length",
    "quiz_accuracy",
    "quiz_frequency",
    "active_days",
    "learning_streak",
    "days_since_last_activity",
    "weekly_sessions",
}

OUTPUT_COLUMNS = [
    "course_id",
    "learner_count",
    "completed_count",
    "dropped_count",
    "completion_rate",
    "dropoff_rate",
    "avg_completion_pct",
    "avg_study_hours",
    "avg_quiz_accuracy",
    "avg_inactivity_days",
    "high_priority_count",
]


def _require_columns(df: pd.DataFrame) -> None:
    """Validate the input contract before course aggregation."""
    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(missing)}"
        )


def _normalise_status(series: pd.Series) -> pd.Series:
    """Return normalized completion status values."""
    return series.astype("string").str.strip().str.lower()


def course_insights(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate learner outcomes and behaviour metrics by course.

    Completion and drop-off rates use the canonical source `status` values:
    `completed` and `dropped`. Behavioural averages come from the existing
    learner insight table.
    """
    _require_columns(df)

    if df.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    insights = build_learner_insights(df).copy()
    insights["status"] = _normalise_status(insights["status"])

    grouped = (
        insights.groupby("course_id", sort=True)
        .agg(
            learner_count=("student_id", "nunique"),
            completed_count=(
                "status",
                lambda values: int(values.eq("completed").sum()),
            ),
            dropped_count=(
                "status",
                lambda values: int(values.eq("dropped").sum()),
            ),
            avg_completion_pct=("completion_pct", "mean"),
            avg_study_hours=("total_study_hours", "mean"),
            avg_quiz_accuracy=("quiz_accuracy", "mean"),
            avg_inactivity_days=("days_since_last_activity", "mean"),
            high_priority_count=(
                "priority",
                lambda values: int(values.eq("high").sum()),
            ),
        )
        .reset_index()
    )

    grouped["completion_rate"] = (
        grouped["completed_count"]
        .div(grouped["learner_count"])
        .mul(100)
    )
    grouped["dropoff_rate"] = (
        grouped["dropped_count"]
        .div(grouped["learner_count"])
        .mul(100)
    )

    rounded_columns = [
        "completion_rate",
        "dropoff_rate",
        "avg_completion_pct",
        "avg_study_hours",
        "avg_quiz_accuracy",
        "avg_inactivity_days",
    ]
    grouped[rounded_columns] = grouped[rounded_columns].round(2)

    return grouped[OUTPUT_COLUMNS].reset_index(drop=True)
