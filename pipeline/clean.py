"""Data cleaning utilities for LearnLens AI."""

from __future__ import annotations

import pandas as pd


def clean_completion(df: pd.DataFrame) -> pd.DataFrame:
	"""Remove duplicates and standardize completion data."""

	df = df.drop_duplicates().copy()
	df["status"] = df["status"].fillna("").astype(str).str.lower().str.strip()
	df["completion_pct"] = pd.to_numeric(df["completion_pct"], errors="coerce").fillna(0)
	return df


def clean_quiz(df: pd.DataFrame) -> pd.DataFrame:
	"""Remove duplicates and standardize quiz data."""

	df = df.drop_duplicates().copy()
	df["score_pct"] = pd.to_numeric(df["score_pct"], errors="coerce").fillna(0)
	df["attempt_number"] = pd.to_numeric(df["attempt_number"], errors="coerce").fillna(0).astype(int)
	return df


def clean_sessions(df: pd.DataFrame) -> pd.DataFrame:
	"""Remove duplicates and standardize session data."""

	df = df.drop_duplicates().copy()
	df["duration_minutes"] = pd.to_numeric(df["duration_minutes"], errors="coerce").fillna(0)
	return df


def clean_enrollment(df: pd.DataFrame) -> pd.DataFrame:
	"""Remove duplicates and standardize enrollment data."""

	return df.drop_duplicates().copy()


def clean_all_data(data_dict: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
	"""Apply the dataset-specific cleaning functions."""

	return {
		"completion": clean_completion(data_dict["completion"]),
		"quiz": clean_quiz(data_dict["quiz"]),
		"sessions": clean_sessions(data_dict["sessions"]),
		"enrollment": clean_enrollment(data_dict["enrollment"]),
	}
