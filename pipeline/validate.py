"""Canonical source schema and dtype validation."""

from __future__ import annotations

import pandas as pd


REQUIRED_SCHEMAS = {
    "completion": (
        "student_id",
        "course_id",
        "completion_pct",
        "status",
    ),
    "quiz": (
        "student_id",
        "course_id",
        "attempt_number",
        "score_pct",
    ),
    "sessions": (
        "student_id",
        "course_id",
        "duration_minutes",
        "start_time",
    ),
    "enrollment": (
        "student_id",
        "course_id",
        "enrollment_date",
        "cohort",
    ),
}

NUMERIC_COLUMNS = {
    "completion": ("completion_pct",),
    "quiz": ("attempt_number", "score_pct"),
    "sessions": ("duration_minutes",),
}

DATETIME_COLUMNS = {
    "completion": (),
    "quiz": ("timestamp",),
    "sessions": ("start_time", "end_time"),
    "enrollment": ("enrollment_date",),
}


def validate_columns(
    df: pd.DataFrame,
    required_cols: tuple[str, ...] | list[str],
    dataset_name: str,
) -> None:
    missing = [
        column for column in required_cols
        if column not in df.columns
    ]
    if missing:
        raise ValueError(
            f"{dataset_name} missing columns: {missing}"
        )


def validate_dtypes(
    df: pd.DataFrame,
    dataset_name: str,
) -> None:
    for column in NUMERIC_COLUMNS.get(dataset_name, ()):
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise TypeError(
                f"{dataset_name}.{column} must be numeric"
            )

        if not pd.Series(df[column]).map(pd.notna).all():
            raise ValueError(
                f"{dataset_name}.{column} contains missing values"
            )

    for column in DATETIME_COLUMNS.get(dataset_name, ()):
        if column not in df.columns:
            continue
        if not pd.api.types.is_datetime64_any_dtype(df[column]):
            raise TypeError(
                f"{dataset_name}.{column} must be datetime-like"
            )


def validate_all(
    data_dict: dict[str, pd.DataFrame],
) -> None:
    unknown = sorted(
        set(data_dict) - set(REQUIRED_SCHEMAS)
    )
    if unknown:
        raise ValueError(
            f"Unknown datasets: {', '.join(unknown)}"
        )

    for name, df in data_dict.items():
        if not isinstance(df, pd.DataFrame):
            raise TypeError(
                f"{name} must be a pandas DataFrame"
            )

        validate_columns(
            df,
            REQUIRED_SCHEMAS[name],
            name,
        )
        validate_dtypes(
            df,
            name,
        )
