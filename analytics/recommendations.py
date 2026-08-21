"""Deterministic learner intervention recommendations.

Recommendations are based on the existing observable learner segments and
behavioural features. They are operational suggestions, not causal claims.
"""

from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = {
    "student_id",
    "course_id",
    "total_study_hours",
    "quiz_accuracy",
    "active_days",
    "days_since_last_activity",
    "weekly_sessions",
    "completion_pct",
}


RECOMMENDATION_MAP = {
    "completed": {
        "action": "completion_follow_up",
        "priority": "low",
        "message": "Course completed; provide a completion acknowledgement and next-course suggestion.",
    },
    "at_risk": {
        "action": "re_engagement",
        "priority": "high",
        "message": "Learner shows prolonged inactivity; send a targeted re-engagement reminder.",
    },
    "high_engagement": {
        "action": "maintain_momentum",
        "priority": "low",
        "message": "Learner is highly engaged; reinforce consistency and suggest the next learning milestone.",
    },
    "struggling_learner": {
        "action": "targeted_practice",
        "priority": "high",
        "message": "Learner is active but quiz performance is low; recommend targeted revision and additional practice.",
    },
    "low_engagement": {
        "action": "engagement_nudge",
        "priority": "medium",
        "message": "Learning activity is low; provide a small achievable study goal and reminder.",
    },
    "consistent_learner": {
        "action": "maintain_consistency",
        "priority": "low",
        "message": "Learner shows consistent activity; reinforce the current study routine.",
    },
}


def _require_columns(df: pd.DataFrame) -> None:
    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(missing)}"
        )


def _validate_numeric_features(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    numeric_columns = [
        "total_study_hours",
        "quiz_accuracy",
        "active_days",
        "days_since_last_activity",
        "weekly_sessions",
        "completion_pct",
    ]

    for column in numeric_columns:
        output[column] = pd.to_numeric(
            output[column],
            errors="coerce",
        )

    if output[numeric_columns].isna().any().any():
        raise ValueError(
            "Recommendation input contains invalid numeric feature values"
        )

    if not output["completion_pct"].between(0, 100).all():
        raise ValueError("completion_pct must be within the range 0-100")

    return output


def _segment_from_row(row: pd.Series) -> str:
    """Mirror the existing segmentation rules used by analytics/segmentation.py."""
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


def generate_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    """Generate one deterministic intervention recommendation per learner.

    The input must contain one row per student-course pair and the behavioural
    features used by the current segmentation rules.
    """
    _require_columns(df)

    columns = [
        "student_id",
        "course_id",
        "segment",
        "action",
        "priority",
        "message",
    ]

    if df.empty:
        return pd.DataFrame(columns=columns)

    output = _validate_numeric_features(df)

    duplicates = output.duplicated(
        subset=["student_id", "course_id"],
        keep=False,
    )
    if duplicates.any():
        raise ValueError(
            "Recommendation input expects one row per student-course pair"
        )

    output["segment"] = output.apply(_segment_from_row, axis=1)

    recommendations = output["segment"].map(RECOMMENDATION_MAP)

    if recommendations.isna().any():
        raise ValueError("No recommendation rule exists for a generated segment")

    output["action"] = recommendations.map(lambda value: value["action"])
    output["priority"] = recommendations.map(lambda value: value["priority"])
    output["message"] = recommendations.map(lambda value: value["message"])

    return output[columns].reset_index(drop=True)


def recommendation_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize recommendation volume and priority for reporting."""
    recommendations = generate_recommendations(df)

    columns = ["priority", "action", "learner_count", "percentage"]

    if recommendations.empty:
        return pd.DataFrame(columns=columns)

    summary = (
        recommendations.groupby(
            ["priority", "action"],
            as_index=False,
        )
        .size()
        .rename(columns={"size": "learner_count"})
    )

    total = int(summary["learner_count"].sum())
    percentages = (
        summary["learner_count"] / total * 100
    ).round(2)

    # Ensure the displayed rounded percentages sum exactly to 100.00.
    rounding_adjustment = round(100.0 - float(percentages.sum()), 2)
    if rounding_adjustment:
        adjustment_index = percentages.idxmax()
        percentages.loc[adjustment_index] = round(
            percentages.loc[adjustment_index] + rounding_adjustment,
            2,
        )

    summary["percentage"] = percentages

    priority_order = pd.Categorical(
        summary["priority"],
        categories=["high", "medium", "low"],
        ordered=True,
    )
    summary = summary.assign(_priority_order=priority_order)

    return (
        summary.sort_values(
            ["_priority_order", "learner_count", "action"],
            ascending=[True, False, True],
        )
        .drop(columns="_priority_order")
        .reset_index(drop=True)
    )
