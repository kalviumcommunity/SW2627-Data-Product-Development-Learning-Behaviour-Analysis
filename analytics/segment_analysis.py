"""Segment-level completion and drop-off analytics."""

from __future__ import annotations

import pandas as pd

from analytics.segmentation import segment_learners


FEATURE_COLUMNS = [
    "student_id",
    "course_id",
    "total_study_hours",
    "quiz_accuracy",
    "days_since_last_activity",
    "completion_pct",
    "status",
]


def _require_columns(df: pd.DataFrame) -> None:
    missing = sorted(set(FEATURE_COLUMNS) - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def _prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    output = df[FEATURE_COLUMNS].copy()

    numeric_columns = [
        "total_study_hours",
        "quiz_accuracy",
        "days_since_last_activity",
        "completion_pct",
    ]

    for column in numeric_columns:
        output[column] = pd.to_numeric(output[column], errors="coerce")

    if output[numeric_columns].isna().any().any():
        raise ValueError(
            "Segment analysis contains invalid numeric feature values"
        )

    output["completion_pct"] = output["completion_pct"].clip(0, 100)
    return output


def _validate_grain(df: pd.DataFrame) -> None:
    duplicates = df.duplicated(
        subset=["student_id", "course_id"],
        keep=False,
    )

    if duplicates.any():
        duplicate_keys = (
            df.loc[duplicates, ["student_id", "course_id"]]
            .drop_duplicates()
            .to_dict("records")
        )
        raise ValueError(
            "Expected one row per student-course pair; "
            f"duplicate keys found: {duplicate_keys}"
        )


def analyze_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate completion/drop-off metrics for each behaviour segment.

    Completion is ``completion_pct >= 100``.
    Drop-off is ``status == 'dropped'``.
    """
    _require_columns(df)

    columns = [
        "segment",
        "learner_count",
        "completion_rate",
        "dropoff_rate",
        "avg_completion_pct",
        "avg_study_hours",
        "avg_quiz_accuracy",
        "avg_days_since_last_activity",
    ]

    if df.empty:
        return pd.DataFrame(columns=columns)

    _validate_grain(df)
    features = _prepare_features(df)

    segments = segment_learners(df)

    segmented = features.merge(
        segments,
        on=["student_id", "course_id"],
        how="left",
        validate="one_to_one",
    )

    if segmented["segment"].isna().any():
        raise ValueError("Failed to assign a behaviour segment")

    segmented["completed"] = segmented["completion_pct"] >= 100
    segmented["dropped"] = (
        segmented["status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("dropped")
    )

    summary = (
        segmented.groupby("segment", as_index=False)
        .agg(
            learner_count=("student_id", "size"),
            completion_rate=("completed", "mean"),
            dropoff_rate=("dropped", "mean"),
            avg_completion_pct=("completion_pct", "mean"),
            avg_study_hours=("total_study_hours", "mean"),
            avg_quiz_accuracy=("quiz_accuracy", "mean"),
            avg_days_since_last_activity=(
                "days_since_last_activity",
                "mean",
            ),
        )
    )

    summary["completion_rate"] = (
        summary["completion_rate"] * 100
    ).round(2)
    summary["dropoff_rate"] = (
        summary["dropoff_rate"] * 100
    ).round(2)

    average_columns = [
        "avg_completion_pct",
        "avg_study_hours",
        "avg_quiz_accuracy",
        "avg_days_since_last_activity",
    ]
    summary[average_columns] = summary[average_columns].round(2)

    return summary.sort_values(
        ["dropoff_rate", "segment"],
        ascending=[False, True],
    ).reset_index(drop=True)
