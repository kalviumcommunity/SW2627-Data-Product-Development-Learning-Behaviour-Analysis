"""Stable analytics outputs for dashboard and CSV consumers.

This module converts the canonical student-course analytics table into
versioned, schema-stable report payloads. It does not recompute analytical
metrics already owned by the analytics modules.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import pandas as pd

ANALYTICS_CONTRACT_VERSION = "1.0"

LEARNER_COLUMNS = [
    "student_id",
    "course_id",
    "status",
    "completion_pct",
    "segment",
    "priority",
    "action",
    "root_cause",
]

COURSE_COLUMNS = [
    "course_id",
    "learner_count",
    "completed_count",
    "dropped_count",
    "completion_rate",
    "dropoff_rate",
    "avg_completion_pct",
    "avg_study_hours",
    "avg_quiz_accuracy",
    "avg_inactivity_days",
    "high_priority_count",
]


@dataclass(frozen=True)
class AnalyticsContract:
    """Version and schema metadata exposed to downstream consumers."""

    version: str
    learner_columns: tuple[str, ...]
    course_columns: tuple[str, ...]


CONTRACT = AnalyticsContract(
    version=ANALYTICS_CONTRACT_VERSION,
    learner_columns=tuple(LEARNER_COLUMNS),
    course_columns=tuple(COURSE_COLUMNS),
)


def contract_metadata() -> dict[str, object]:
    """Return JSON-serializable contract metadata."""
    return asdict(CONTRACT)


def _require_columns(
    frame: pd.DataFrame,
    required: list[str],
    dataset_name: str,
) -> None:
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(
            f"{dataset_name} is missing required columns: "
            + ", ".join(missing)
        )


def _normalized_learner_output(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize learner records to the published frontend contract."""
    _require_columns(
        frame,
        LEARNER_COLUMNS,
        "learner analytics",
    )

    output = frame[LEARNER_COLUMNS].copy()

    for column in ["student_id", "course_id", "status", "segment",
                   "priority", "action", "root_cause"]:
        output[column] = output[column].astype("string").str.strip()

    output["status"] = (
        output["status"]
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    output["completion_pct"] = pd.to_numeric(
        output["completion_pct"],
        errors="coerce",
    ).round(2)

    if output["completion_pct"].isna().any():
        raise ValueError(
            "learner analytics contains invalid completion_pct values"
        )

    if not output["completion_pct"].between(0, 100).all():
        raise ValueError(
            "learner analytics completion_pct must be within 0-100"
        )

    if output[["student_id", "course_id"]].isna().any().any():
        raise ValueError(
            "learner analytics identifiers cannot be missing"
        )

    if output.duplicated(
        ["student_id", "course_id"],
        keep=False,
    ).any():
        raise ValueError(
            "learner analytics must contain one row per student-course pair"
        )

    return (
        output.sort_values(
            ["course_id", "student_id"],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def learner_export(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Return the stable learner-level CSV contract."""
    return _normalized_learner_output(frame)


def course_export(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Return the stable course-level CSV contract."""
    _require_columns(frame, COURSE_COLUMNS, "course analytics")

    output = frame[COURSE_COLUMNS].copy()

    output["course_id"] = output["course_id"].astype("string").str.strip()

    integer_columns = [
        "learner_count",
        "completed_count",
        "dropped_count",
        "high_priority_count",
    ]
    numeric_columns = [
        "completion_rate",
        "dropoff_rate",
        "avg_completion_pct",
        "avg_study_hours",
        "avg_quiz_accuracy",
        "avg_inactivity_days",
    ]

    for column in integer_columns:
        output[column] = pd.to_numeric(
            output[column],
            errors="raise",
        ).astype("int64")

    for column in numeric_columns:
        output[column] = pd.to_numeric(
            output[column],
            errors="coerce",
        ).round(2)

    if output.isna().any().any():
        raise ValueError(
            "course analytics contains missing contract values"
        )

    for column in [
        "completion_rate",
        "dropoff_rate",
        "avg_completion_pct",
        "avg_quiz_accuracy",
    ]:
        if not output[column].between(0, 100).all():
            raise ValueError(
                f"{column} must be within the range 0-100"
            )

    if (output[integer_columns] < 0).any().any():
        raise ValueError(
            "course analytics count fields cannot be negative"
        )

    return output.sort_values(
        "course_id",
        kind="stable",
    ).reset_index(drop=True)


def export_csv(
    frame: pd.DataFrame,
    output_path: str | Path,
    *,
    level: str = "learner",
) -> Path:
    """Write a contract-compliant CSV and return its path."""
    output = Path(output_path)

    if level == "learner":
        normalized = learner_export(frame)
    elif level == "course":
        normalized = course_export(frame)
    else:
        raise ValueError(
            "level must be either 'learner' or 'course'"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(output, index=False)

    return output


def export_contract_metadata(
    output_path: str | Path,
) -> Path:
    """Write the published analytics contract metadata as JSON."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        json.dumps(
            contract_metadata(),
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    return output
