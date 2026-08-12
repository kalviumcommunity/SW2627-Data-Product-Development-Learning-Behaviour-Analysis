"""Data validation utilities for LearnLens AI."""

from __future__ import annotations

import pandas as pd


REQUIRED_SCHEMAS: dict[str, list[str]] = {
	"completion": ["student_id", "course_id", "completion_pct", "status"],
	"quiz": ["student_id", "quiz_id", "course_id", "attempt_number", "score_pct", "timestamp"],
	"sessions": ["session_id", "student_id", "course_id", "start_time", "end_time", "duration_minutes"],
	"enrollment": ["student_id", "course_id", "enrollment_date", "cohort"],
}

NUMERIC_COLUMNS: dict[str, list[str]] = {
	"completion": ["completion_pct"],
	"quiz": ["attempt_number", "score_pct"],
	"sessions": ["duration_minutes"],
}


def validate_columns(df: pd.DataFrame, required_cols: list[str], dataset_name: str) -> None:
	"""Ensure a dataset contains all required columns."""

	missing = [col for col in required_cols if col not in df.columns]
	if missing:
		raise ValueError(f"{dataset_name} missing columns: {missing}")


def validate_dtypes(df: pd.DataFrame, dataset_name: str) -> None:
	"""Check the basic numeric columns used by the pipeline."""

	for column in NUMERIC_COLUMNS.get(dataset_name, []):
		if column in df.columns and not pd.api.types.is_numeric_dtype(df[column]):
			raise TypeError(f"{dataset_name}.{column} must be numeric")


def validate_all(data_dict: dict[str, pd.DataFrame]) -> None:
	"""Validate every dataset in the ingestion dictionary."""

	for name, df in data_dict.items():
		validate_columns(df, REQUIRED_SCHEMAS[name], name)
		validate_dtypes(df, name)
