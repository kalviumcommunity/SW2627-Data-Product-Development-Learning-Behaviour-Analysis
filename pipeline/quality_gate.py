# pipeline/quality_gate.py
"""Lightweight quality gate utilities used by the pipeline tests."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd


def _count_invalid_ids(df: pd.DataFrame, id_columns=("student_id", "course_id")) -> int:
    """Count rows with missing/empty student_id or course_id (treat empty string as invalid)."""

    if not set(id_columns).issubset(df.columns):
        return len(df)

    invalid = (
        df[list(id_columns)].isna().any(axis=1)
        | (df[list(id_columns)]
           .astype(str)
           .apply(lambda s: s.str.strip())
           .eq("")
          ).any(axis=1)
    )

    return int(invalid.sum())


def validate_pipeline_output(
    source_datasets: Dict[str, pd.DataFrame],
    student_course_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Validate source datasets and the final student_course dataframe.

    Returns a DataFrame report with columns:
      - dataset
      - row_count
      - missing_values (total missing cell count)
      - duplicate_rows (number of duplicate full rows)
      - invalid_id_rows (rows with missing/empty student_id or course_id)
      - valid (bool)

    Raises ValueError to block the pipeline for fatal issues:
      - any source dataset with invalid ID rows (empty student_id or course_id)
      - duplicate student-course keys in student_course_df
      - completion_pct outside 0-100 in student_course_df (if column present)
    """
    reports = []

    # Validate each source dataset
    for name, df in source_datasets.items():
        # Ensure df is a DataFrame
        if not isinstance(df, pd.DataFrame):
            raise TypeError("source_datasets values must be pandas DataFrame")

        row_count = len(df)
        missing_values = int(df.isnull().sum().sum())
        duplicate_rows = int(df.duplicated().sum())
        invalid_id_rows = _count_invalid_ids(df)

        valid = (invalid_id_rows == 0)

        reports.append(
            {
                "dataset": name,
                "row_count": row_count,
                "missing_values": missing_values,
                "duplicate_rows": duplicate_rows,
                "invalid_id_rows": invalid_id_rows,
                "valid": valid,
            }
        )

        # If a source dataset has invalid id rows, block the pipeline
        if invalid_id_rows > 0:
            raise ValueError(f"data-quality checks failed: {name} contains invalid IDs")

    report_df = pd.DataFrame(reports)

    # Validate student_course_df
    if not isinstance(student_course_df, pd.DataFrame):
        raise TypeError("student_course_df must be a pandas DataFrame")

    # 1. duplicate student-course keys
    if {"student_id", "course_id"}.issubset(student_course_df.columns):
        dup_keys = student_course_df.duplicated(subset=["student_id", "course_id"]).sum()
        if int(dup_keys) > 0:
            raise ValueError("duplicate student-course keys found in student_course_df")
    else:
        # if columns missing, consider this fatal
        raise ValueError("student_course_df missing required student_id or course_id columns")

    # 2. check completion_pct range if present
    if "completion_pct" in student_course_df.columns:
        # Allow NaN (missing), but if a numeric cell exists, ensure 0 <= value <= 100
        # If non-numeric values exist, attempt coercion and then test range
        comp = pd.to_numeric(student_course_df["completion_pct"], errors="coerce")
        invalid_range = comp.dropna().lt(0).any() or comp.dropna().gt(100).any()
        if invalid_range:
            raise ValueError("student_course_df completion_pct values out of expected range 0-100")

    return report_df


def write_quality_report(report: pd.DataFrame, output_path: Path) -> Path:
    """
    Write a quality report DataFrame to CSV. Returns the Path to the saved file.

    Raises TypeError if `report` is not a pandas DataFrame.
    """
    if not isinstance(report, pd.DataFrame):
        raise TypeError("report must be a pandas DataFrame")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(output_path, index=False)
    return output_path