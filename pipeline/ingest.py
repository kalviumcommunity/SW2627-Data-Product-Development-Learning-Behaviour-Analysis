"""Data ingestion utilities for LearnLens."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pipeline.config import (
    BASE_DATA_PATH,
    DATA_SOURCE_MODE,
    SYNTHETIC_COURSES,
    SYNTHETIC_DAYS,
    SYNTHETIC_PERSIST,
    SYNTHETIC_SEED_ENV,
    SYNTHETIC_START_DATE,
)
from pipeline.synthetic_data import (
    SyntheticDataConfig,
    generate_synthetic_datasets,
    write_synthetic_snapshot,
)


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load one CSV file with a useful missing-file error."""
    path = Path(path)

    try:
        return pd.read_csv(path)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Input file not found: {path}"
        ) from exc


def _synthetic_seed() -> int | None:
    if SYNTHETIC_SEED_ENV is None:
        return None

    try:
        return int(SYNTHETIC_SEED_ENV)
    except ValueError as exc:
        raise ValueError(
            "LEARNLENS_SYNTHETIC_SEED must be an integer"
        ) from exc


def load_synthetic_data() -> dict[str, pd.DataFrame]:
    """Generate a fresh synthetic dataset for the current pipeline run."""
    config = SyntheticDataConfig(
        seed=_synthetic_seed(),
        students=SYNTHETIC_STUDENTS,
        courses=SYNTHETIC_COURSES,
        days=SYNTHETIC_DAYS,
        start_date=SYNTHETIC_START_DATE,
    )

    datasets = generate_synthetic_datasets(config)

    if SYNTHETIC_PERSIST:
        write_synthetic_snapshot(
            BASE_DATA_PATH.parent / "generated",
            datasets,
            seed=config.seed,
            config=config,
        )

    return datasets


def load_all_data(
    data_path: str | Path = BASE_DATA_PATH,
) -> dict[str, pd.DataFrame]:
    """Load pipeline inputs according to the configured source mode.

    Synthetic generation is the default. CSV ingestion remains available via
    ``LEARNLENS_DATA_SOURCE=csv`` for externally supplied datasets.
    """
    if DATA_SOURCE_MODE == "synthetic":
        return load_synthetic_data()

    if DATA_SOURCE_MODE == "csv":
        base_dir = Path(data_path)

        return {
            "completion": load_csv(
                base_dir / "completion.csv"
            ),
            "quiz": load_csv(
                base_dir / "quiz.csv"
            ),
            "sessions": load_csv(
                base_dir / "sessions.csv"
            ),
            "enrollment": load_csv(
                base_dir / "enrollment.csv"
            ),
        }

    raise ValueError(
        "LEARNLENS_DATA_SOURCE must be either "
        "'synthetic' or 'csv'"
    )
