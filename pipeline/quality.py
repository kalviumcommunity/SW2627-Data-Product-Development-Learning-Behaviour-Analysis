"""Canonical data-quality checks for LearnLens pipeline datasets."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd


KEYS = ("student_id", "course_id")

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


def _invalid_id_rows(df: pd.DataFrame) -> int:
    invalid = pd.Series(False, index=df.index)

    for column in KEYS:
        if column not in df.columns:
            continue
        invalid |= df[column].isna()
        invalid |= (
            df[column]
            .astype("string")
            .str.strip()
            .eq("")
            .fillna(False)
        )

    return int(invalid.sum()) if len(df) else 0


def _domain_error(df: pd.DataFrame, dataset: str) -> bool:
    if dataset == "completion" and "completion_pct" in df.columns:
        values = pd.to_numeric(df["completion_pct"], errors="coerce")
        numbers = values.to_numpy(dtype=float)
        return bool(
            values.isna().any()
            or not np.isfinite(numbers).all()
            or not values.between(0, 100).all()
        )

    if dataset == "quiz":
        if "attempt_number" in df.columns:
            values = pd.to_numeric(
                df["attempt_number"],
                errors="coerce",
            )
            numbers = values.to_numpy(dtype=float)
            if (
                values.isna().any()
                or not np.isfinite(numbers).all()
                or not values.ge(1).all()
            ):
                return True

        if "score_pct" in df.columns:
            values = pd.to_numeric(
                df["score_pct"],
                errors="coerce",
            )
            numbers = values.to_numpy(dtype=float)
            if (
                values.isna().any()
                or not np.isfinite(numbers).all()
                or not values.between(0, 100).all()
            ):
                return True

    if dataset == "sessions" and "duration_minutes" in df.columns:
        values = pd.to_numeric(
            df["duration_minutes"],
            errors="coerce",
        )
        numbers = values.to_numpy(dtype=float)
        return bool(
            values.isna().any()
            or not np.isfinite(numbers).all()
            or not values.ge(0).all()
        )

    return False


def generate_quality_report(
    data: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Return the legacy, stable quality-report schema."""
    rows: list[dict[str, object]] = []

    for name, df in data.items():
        if not isinstance(df, pd.DataFrame):
            raise TypeError(
                f"{name} must be a pandas DataFrame"
            )

        missing = int(df.isna().sum().sum())
        duplicates = int(df.duplicated(keep=False).sum())
        invalid_ids = _invalid_id_rows(df)

        rows.append(
            {
                "dataset": name,
                "row_count": len(df),
                "missing_values": missing,
                "duplicate_rows": duplicates,
                "invalid_id_rows": invalid_ids,
                "valid": bool(
                    len(df) > 0
                    and missing == 0
                    and duplicates == 0
                    and invalid_ids == 0
                    and not _domain_error(df, name)
                ),
            }
        )

    return pd.DataFrame(
        rows,
        columns=[
            "dataset",
            "row_count",
            "missing_values",
            "duplicate_rows",
            "invalid_id_rows",
            "valid",
        ],
    )


def validate_student_course_table(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Validate the final one-row-per-student-course analytics table."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "student_course must be a pandas DataFrame"
        )

    missing = [
        column for column in KEYS
        if column not in df.columns
    ]
    if missing:
        raise ValueError(
            "student_course missing columns: "
            + ", ".join(missing)
        )

    invalid_ids = _invalid_id_rows(df)
    if invalid_ids:
        raise ValueError(
            f"student_course contains {invalid_ids} rows "
            "with missing or blank identifiers"
        )

    duplicates = int(
        df.duplicated(
            subset=list(KEYS),
            keep=False,
        ).sum()
    )
    if duplicates:
        raise ValueError(
            f"student_course contains {duplicates} rows "
            "with duplicate student-course keys"
        )

    for column in ("completion_pct", "quiz_accuracy"):
        if column not in df.columns:
            continue

        values = pd.to_numeric(
            df[column],
            errors="coerce",
        )
        numeric = values.to_numpy(dtype=float)

        invalid = (
            values.isna()
            | ~values.between(0, 100)
            | ~np.isfinite(numeric)
        )

        if invalid.any():
            raise ValueError(
                f"student_course.{column} contains "
                f"{int(invalid.sum())} invalid values; "
                "expected finite values in range 0-100"
            )

    return df
