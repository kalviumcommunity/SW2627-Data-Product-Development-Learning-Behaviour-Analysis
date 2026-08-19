"""Data ingestion utilities for LearnLens AI."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pipeline.config import BASE_DATA_PATH


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load a CSV file and raise a useful error when it does not exist."""
    path = Path(path)

    try:
        return pd.read_csv(path)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Input file not found: {path}") from exc


def load_all_data(
    data_path: str | Path = BASE_DATA_PATH,
) -> dict[str, pd.DataFrame]:
    """Load all MVP source datasets from the supplied raw-data directory."""
    base_dir = Path(data_path)

    return {
        "completion": load_csv(base_dir / "completion.csv"),
        "quiz": load_csv(base_dir / "quiz.csv"),
        "sessions": load_csv(base_dir / "sessions.csv"),
        "enrollment": load_csv(base_dir / "enrollment.csv"),
    }
