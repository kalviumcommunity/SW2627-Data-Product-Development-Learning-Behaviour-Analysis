"""Explainable root-cause signals for learner drop-off analysis."""
from __future__ import annotations

import pandas as pd

from analytics.segmentation import segment_learners

REQUIRED_COLUMNS = {
    "student_id", "course_id", "total_study_hours", "quiz_accuracy",
    "active_days", "learning_streak", "days_since_last_activity",
    "weekly_sessions", "completion_pct",
}

OUTPUT_COLUMNS = [
    "student_id", "course_id", "segment", "root_cause", "priority", "evidence",
]

ROOT_CAUSE_PRIORITY = {
    "completed": "low",
    "inactivity": "high",
    "performance": "high",
    "engagement": "medium",
    "mixed": "high",
    "no_clear_driver": "low",
}


def _require_columns(df: pd.DataFrame) -> None:
    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    numeric = [
        "total_study_hours", "quiz_accuracy", "active_days",
        "learning_streak", "days_since_last_activity",
        "weekly_sessions", "completion_pct",
    ]

    for column in numeric:
        output[column] = pd.to_numeric(output[column], errors="coerce")

    if output[numeric].isna().any().any():
        raise ValueError(
            "Root-cause analysis contains invalid numeric feature values"
        )

    if not output["completion_pct"].between(0, 100).all():
        raise ValueError("completion_pct must be within the range 0-100")

    return output


def _validate_grain(df: pd.DataFrame) -> None:
    if df.duplicated(
        ["student_id", "course_id"],
        keep=False,
    ).any():
        raise ValueError(
            "Root-cause analysis expects one row per student-course pair"
        )


def _classify(row: pd.Series) -> tuple[str, str]:
    if row["completion_pct"] >= 100:
        return "completed", "Course completion has reached 100%."

    inactivity = row["days_since_last_activity"] >= 14
    low_activity = (
        row["active_days"] <= 2
        or row["weekly_sessions"] < 1
    )
    low_performance = row["quiz_accuracy"] < 50

    if (inactivity or low_activity) and low_performance:
        engagement_evidence = (
            "14+ days since last activity"
            if inactivity
            else "low active-day/session frequency"
        )
        return (
            "mixed",
            f"{engagement_evidence}; quiz accuracy below 50%.",
        )

    if inactivity:
        return "inactivity", "14+ days since last activity."

    if low_performance:
        return (
            "performance",
            "Quiz accuracy is below 50% while engagement is present.",
        )

    if low_activity:
        return (
            "engagement",
            "Active days or weekly session frequency is low.",
        )

    return (
        "no_clear_driver",
        "No predefined inactivity, performance, or engagement signal dominates.",
    )


def analyze_root_causes(df: pd.DataFrame) -> pd.DataFrame:
    """Classify one observable behavioural driver per learner record.

    The classification is descriptive and must not be interpreted as causal
    attribution.
    """
    _require_columns(df)

    if df.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    prepared = _prepare(df)
    _validate_grain(prepared)

    segments = segment_learners(prepared)

    classified = prepared.apply(
        _classify,
        axis=1,
        result_type="expand",
    )
    classified.columns = ["root_cause", "evidence"]

    result = pd.concat(
        [
            prepared[["student_id", "course_id"]].reset_index(drop=True),
            segments[["segment"]].reset_index(drop=True),
            classified.reset_index(drop=True),
        ],
        axis=1,
    )

    result["priority"] = result["root_cause"].map(ROOT_CAUSE_PRIORITY)

    if result["priority"].isna().any():
        raise ValueError(
            "Root-cause classification produced an unsupported driver"
        )

    return result[OUTPUT_COLUMNS].reset_index(drop=True)


def root_cause_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize learner counts and percentages by observable driver."""
    classified = analyze_root_causes(df)
    columns = ["root_cause", "priority", "learner_count", "percentage"]

    if classified.empty:
        return pd.DataFrame(columns=columns)

    summary = (
        classified.groupby(
            ["root_cause", "priority"],
            as_index=False,
        )
        .size()
        .rename(columns={"size": "learner_count"})
    )

    total = int(summary["learner_count"].sum())
    percentages = (
        summary["learner_count"] / total * 100
    ).round(2)

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
            ["_priority_order", "learner_count", "root_cause"],
            ascending=[True, False, True],
        )
        .drop(columns="_priority_order")
        .reset_index(drop=True)
    )
