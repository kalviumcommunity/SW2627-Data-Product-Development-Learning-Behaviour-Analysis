"""Rule-based learner behaviour segmentation.

The segmentation layer converts student-course behavioural features into
deterministic, explainable learner segments.
"""

from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = {
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


def _require_columns(df: pd.DataFrame) -> None:
    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def _segment_row(row: pd.Series) -> str:
    """Assign one deterministic behaviour segment to a learner."""
    completion = float(row["completion_pct"])
    quiz_accuracy = float(row["quiz_accuracy"])
    active_days = float(row["active_days"])
    study_hours = float(row["total_study_hours"])
    inactivity = float(row["days_since_last_activity"])
    weekly_sessions = float(row["weekly_sessions"])
    streak = float(row["learning_streak"])

    if completion >= 100:
        return "completed"

    if inactivity >= 14:
        return "at_risk"

    if (
        study_hours >= 5
        and quiz_accuracy >= 75
        and active_days >= 5
    ):
        return "high_engagement"

    if quiz_accuracy < 50 and (
        active_days >= 2 or weekly_sessions >= 1
    ):
        return "struggling_learner"

    if active_days <= 2 or weekly_sessions < 1:
        return "low_engagement"

    if streak >= 2 or weekly_sessions >= 1.5:
        return "consistent_learner"

    return "low_engagement"


def segment_learners(df: pd.DataFrame) -> pd.DataFrame:
    """Return one deterministic segment for each student-course row."""
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
        output[column] = pd.to_numeric(output[column], errors="coerce")

    if output.empty:
        output["segment"] = pd.Series(dtype="object")
        return output[
            ["student_id", "course_id", "segment"]
        ].reset_index(drop=True)

    if output[numeric_columns].isna().any().any():
        raise ValueError(
            "Behavioural feature columns contain invalid numeric values"
        )

    output["segment"] = output.apply(_segment_row, axis=1)

    return output[
        ["student_id", "course_id", "segment"]
    ].reset_index(drop=True)
