"""Deterministic learner intervention recommendations.

Recommendations are derived from the canonical learner segmentation layer and
the same behavioural feature contract used elsewhere in analytics.
"""

from __future__ import annotations

import pandas as pd

from analytics.segmentation import segment_learners


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


RECOMMENDATION_MAP = {
    "completed": {
        "action": "completion_follow_up",
        "priority": "low",
        "message": (
            "Course completed; provide a completion acknowledgement "
            "and next-course suggestion."
        ),
    },
    "at_risk": {
        "action": "re_engagement",
        "priority": "high",
        "message": (
            "Learner shows prolonged inactivity; send a targeted "
            "re-engagement reminder."
        ),
    },
    "high_engagement": {
        "action": "maintain_momentum",
        "priority": "low",
        "message": (
            "Learner is highly engaged; reinforce consistency and "
            "suggest the next learning milestone."
        ),
    },
    "struggling_learner": {
        "action": "targeted_practice",
        "priority": "high",
        "message": (
            "Learner is active but quiz performance is low; recommend "
            "targeted revision and additional practice."
        ),
    },
    "low_engagement": {
        "action": "engagement_nudge",
        "priority": "medium",
        "message": (
            "Learning activity is low; provide a small achievable "
            "study goal and reminder."
        ),
    },
    "consistent_learner": {
        "action": "maintain_consistency",
        "priority": "low",
        "message": (
            "Learner shows consistent activity; reinforce the current "
            "study routine."
        ),
    },
}


def _require_columns(df: pd.DataFrame) -> None:
    """Validate the feature columns needed by segmentation."""
    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(missing)}"
        )


def _validate_input(df: pd.DataFrame) -> pd.DataFrame:
    """Return a normalized copy suitable for segmentation."""
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
            output[column],
            errors="coerce",
        )

    if output[numeric_columns].isna().any().any():
        raise ValueError(
            "Recommendation input contains invalid numeric feature values"
        )

    if not output["completion_pct"].between(0, 100).all():
        raise ValueError(
            "completion_pct must be within the range 0-100"
        )

    return output


def _validate_grain(df: pd.DataFrame) -> None:
    """Ensure one row exists per student-course pair."""
    duplicates = df.duplicated(
        subset=["student_id", "course_id"],
        keep=False,
    )

    if duplicates.any():
        raise ValueError(
            "Recommendation input expects one row per student-course pair"
        )


def generate_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    """Generate one deterministic recommendation per student-course row.

    Segments are assigned exclusively by ``segment_learners()`` so the
    recommendation layer has a single segmentation source of truth.
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

    output = _validate_input(df)
    _validate_grain(output)

    segmented = segment_learners(output)

    recommendations = segmented["segment"].map(RECOMMENDATION_MAP)
    if recommendations.isna().any():
        unknown = sorted(
            segmented.loc[
                recommendations.isna(),
                "segment",
            ].astype(str).unique()
        )
        raise ValueError(
            "No recommendation rule exists for segment(s): "
            + ", ".join(unknown)
        )

    result = segmented.copy()
    result["action"] = recommendations.map(
        lambda value: value["action"]
    )
    result["priority"] = recommendations.map(
        lambda value: value["priority"]
    )
    result["message"] = recommendations.map(
        lambda value: value["message"]
    )

    return result[columns].reset_index(drop=True)


def recommendation_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize recommendation volume and percentage by action."""
    recommendations = generate_recommendations(df)

    columns = [
        "priority",
        "action",
        "learner_count",
        "percentage",
    ]

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

    # Reconcile rounding so dashboard percentages always total 100.00.
    adjustment = round(100.0 - float(percentages.sum()), 2)
    if adjustment:
        target = percentages.idxmax()
        percentages.loc[target] = round(
            percentages.loc[target] + adjustment,
            2,
        )

    summary["percentage"] = percentages

    priority_order = pd.Categorical(
        summary["priority"],
        categories=["high", "medium", "low"],
        ordered=True,
    )

    return (
        summary.assign(_priority_order=priority_order)
        .sort_values(
            ["_priority_order", "learner_count", "action"],
            ascending=[True, False, True],
        )
        .drop(columns="_priority_order")
        .reset_index(drop=True)
    )
