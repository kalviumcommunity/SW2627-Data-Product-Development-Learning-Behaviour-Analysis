"""Data ingestion utilities for LearnLens AI."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_csv(path: str) -> pd.DataFrame:
	"""Read a CSV file into a DataFrame."""

	try:
		return pd.read_csv(path)
	except FileNotFoundError as exc:
		raise FileNotFoundError(f"File not found: {path}") from exc


def load_all_data(base_path: str = "data/raw") -> dict[str, pd.DataFrame]:
	"""Load all raw datasets from a base directory."""

	base_dir = Path(base_path)
	return {
		"completion": load_csv(str(base_dir / "completion.csv")),
		"quiz": load_csv(str(base_dir / "quiz.csv")),
		"sessions": load_csv(str(base_dir / "sessions.csv")),
		"enrollment": load_csv(str(base_dir / "enrollment.csv")),
	}


def run_pipeline(base_path: str = "data/raw") -> dict[str, pd.DataFrame]:
	"""Load, validate, and clean the raw datasets."""

	from pipeline.clean import clean_all_data
	from pipeline.validate import validate_all

	data = load_all_data(base_path)
	validate_all(data)
	return clean_all_data(data)
