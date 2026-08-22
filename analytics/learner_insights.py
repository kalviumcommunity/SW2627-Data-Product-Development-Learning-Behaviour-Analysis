"""Dashboard-ready learner insight table."""
from __future__ import annotations

import pandas as pd

from analytics.recommendations import generate_recommendations

REQUIRED_COLUMNS = {
    "student_id", "course_id", "status", "completion_pct",
    "total_study_hours", "avg_session_length", "quiz_accuracy",
    "quiz_frequency", "active_days", "learning_streak",
    "days_since_last_activity", "weekly_sessions",
}

OUTPUT_COLUMNS = [
    "student_id", "course_id", "status", "completion_pct",
    "total_study_hours", "avg_session_length", "quiz_accuracy",
    "quiz_frequency", "active_days", "learning_streak",
    "days_since_last_activity", "weekly_sessions",
    "segment", "action", "priority", "message",
]


def _require_columns(df: pd.DataFrame) -> None:
    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def _validate_input(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    numeric = [
        "total_study_hours", "avg_session_length", "quiz_accuracy",
        "quiz_frequency", "active_days", "learning_streak",
        "days_since_last_activity", "weekly_sessions", "completion_pct",
    ]
    for column in numeric:
        output[column] = pd.to_numeric(output[column], errors="coerce")
    if output[numeric].isna().any().any():
        raise ValueError("Learner insights contain invalid numeric feature values")
    if not output["quiz_accuracy"].between(0, 100).all():
        raise ValueError("quiz_accuracy must be within the range 0-100")
    if not output["completion_pct"].between(0, 100).all():
        raise ValueError("completion_pct must be within the range 0-100")
    return output


def _validate_grain(df: pd.DataFrame) -> None:
    if df.duplicated(["student_id", "course_id"], keep=False).any():
        raise ValueError(
            "Learner insights expect one row per student-course pair"
        )


def build_learner_insights(df: pd.DataFrame) -> pd.DataFrame:
    """Compose behavioural features with canonical recommendations."""
    _require_columns(df)
    if df.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    output = _validate_input(df)
    _validate_grain(output)

    recommendations = generate_recommendations(output)

    result = output[
        [
            "student_id", "course_id", "status", "completion_pct",
            "total_study_hours", "avg_session_length", "quiz_accuracy",
            "quiz_frequency", "active_days", "learning_streak",
            "days_since_last_activity", "weekly_sessions",
        ]
    ].merge(
        recommendations,
        on=["student_id", "course_id"],
        how="left",
        validate="one_to_one",
    )

    if result[["segment", "action", "priority", "message"]].isna().any().any():
        raise ValueError("Failed to generate complete learner insight records")

    return (
        result[OUTPUT_COLUMNS]
        .sort_values(["course_id", "student_id"])
        .reset_index(drop=True)
    )


def insight_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize learner counts by segment and recommendation priority."""
    insights = build_learner_insights(df)
    columns = ["segment", "priority", "learner_count", "percentage"]
    if insights.empty:
        return pd.DataFrame(columns=columns)

    summary = (
        insights.groupby(["segment", "priority"], as_index=False)
        .size()
        .rename(columns={"size": "learner_count"})
    )
    total = int(summary["learner_count"].sum())
    percentages = (summary["learner_count"] / total * 100).round(2)

    adjustment = round(100.0 - float(percentages.sum()), 2)
    if adjustment:
        target = percentages.idxmax()
        percentages.loc[target] = round(
            percentages.loc[target] + adjustment, 2
        )
    summary["percentage"] = percentages

    order = pd.Categorical(
        summary["priority"],
        categories=["high", "medium", "low"],
        ordered=True,
    )
    return (
        summary.assign(_priority_order=order)
        .sort_values(
            ["_priority_order", "learner_count", "segment"],
            ascending=[True, False, True],
        )
        .drop(columns="_priority_order")
        .reset_index(drop=True)
    )
