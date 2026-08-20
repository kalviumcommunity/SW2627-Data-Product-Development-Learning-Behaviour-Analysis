"""Data-quality checks for LearnLens pipeline datasets."""
from __future__ import annotations
from collections.abc import Mapping
import pandas as pd

KEYS = ("student_id", "course_id")

def _invalid_id_rows(df: pd.DataFrame) -> int:
    invalid = pd.Series(False, index=df.index)
    for col in KEYS:
        if col not in df:
            continue
        invalid |= df[col].isna()
        if pd.api.types.is_string_dtype(df[col]):
            invalid |= df[col].astype("string").str.strip().eq("").fillna(False)
    return int(invalid.sum()) if len(df) else 0

def generate_quality_report(data: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """Return safe, aggregate data-quality metrics for each dataset."""
    rows = []
    for name, df in data.items():
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"{name} must be a pandas DataFrame")
        missing = int(df.isna().sum().sum())
        duplicates = int(df.duplicated(keep=False).sum())
        invalid_ids = _invalid_id_rows(df)
        rows.append({
            "dataset": name,
            "row_count": len(df),
            "missing_values": missing,
            "duplicate_rows": duplicates,
            "invalid_id_rows": invalid_ids,
            "valid": bool(
                len(df) > 0 and missing == 0 and
                duplicates == 0 and invalid_ids == 0
            ),
        })
    return pd.DataFrame(rows, columns=[
        "dataset", "row_count", "missing_values", "duplicate_rows",
        "invalid_id_rows", "valid",
    ])

def validate_student_course_table(df: pd.DataFrame) -> pd.DataFrame:
    """Validate the final one-row-per-student-course analytics handoff."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("student_course must be a pandas DataFrame")

    missing = [c for c in KEYS if c not in df.columns]
    if missing:
        raise ValueError("student_course missing columns: " + ", ".join(missing))

    invalid_ids = _invalid_id_rows(df)
    if invalid_ids:
        raise ValueError(
            f"student_course contains {invalid_ids} rows with missing or blank identifiers"
        )

    duplicate_keys = int(df.duplicated(subset=list(KEYS), keep=False).sum())
    if duplicate_keys:
        raise ValueError(
            f"student_course contains {duplicate_keys} rows with duplicate student-course keys"
        )

    for col in ("completion_pct", "quiz_accuracy"):
        if col not in df.columns:
            continue
        values = pd.to_numeric(df[col], errors="coerce")
        invalid = values.isna() | ~values.between(0, 100)
        if invalid.any():
            raise ValueError(
                f"student_course.{col} contains {int(invalid.sum())} invalid values; expected range 0-100"
            )
    return df
