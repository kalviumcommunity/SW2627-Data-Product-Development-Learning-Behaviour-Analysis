"""Data ingestion utilities for LearnLens AI."""

from pathlib import Path
import pandas as pd


def load_csv(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {path}")


def load_all_data(base_path: str = "data/raw") -> dict:
    base_dir = Path(base_path)

    return {
        "completion": load_csv(base_dir / "completion.csv"),
        "quiz": load_csv(base_dir / "quiz.csv"),
        "sessions": load_csv(base_dir / "sessions.csv"),
        "enrollment": load_csv(base_dir / "enrollment.csv"),
    }