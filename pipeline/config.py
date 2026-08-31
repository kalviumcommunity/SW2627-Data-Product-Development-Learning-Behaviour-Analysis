"""Runtime configuration for the LearnLens pipeline."""

from __future__ import annotations

import os
from pathlib import Path


BASE_DATA_PATH = Path(
    os.getenv(
        "LEARNLENS_RAW_DATA_PATH",
        "data/raw",
    )
)

PROCESSED_PATH = Path(
    os.getenv(
        "LEARNLENS_PROCESSED_PATH",
        "data/processed",
    )
)

# Synthetic generation is the default so the application has no dependency
# on committed/hardcoded raw CSV fixtures. Set to "csv" to explicitly use
# externally supplied raw data.
DATA_SOURCE_MODE = os.getenv(
    "LEARNLENS_DATA_SOURCE",
    "synthetic",
).strip().lower()

SYNTHETIC_SEED_ENV = os.getenv(
    "LEARNLENS_SYNTHETIC_SEED"
)

SYNTHETIC_STUDENTS = int(
    os.getenv(
        "LEARNLENS_SYNTHETIC_STUDENTS",
        "100",
    )
)

SYNTHETIC_COURSES = int(
    os.getenv(
        "LEARNLENS_SYNTHETIC_COURSES",
        "5",
    )
)

SYNTHETIC_DAYS = int(
    os.getenv(
        "LEARNLENS_SYNTHETIC_DAYS",
        "90",
    )
)

SYNTHETIC_START_DATE = os.getenv(
    "LEARNLENS_SYNTHETIC_START_DATE",
    "2024-01-01",
)

SYNTHETIC_PERSIST = (
    os.getenv(
        "LEARNLENS_SYNTHETIC_PERSIST",
        "false",
    ).strip().lower()
    in {"1", "true", "yes", "on"}
)
