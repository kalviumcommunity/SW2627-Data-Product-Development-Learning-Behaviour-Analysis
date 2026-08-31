"""Stable analytics outputs for dashboard and CSV consumers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import pandas as pd

from pipeline.quality import validate_student_course_table

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

ALLOWED_SEGMENTS = frozenset({
    "completed",
    "at_risk",
    "struggling_learner",
    "low_engagement",
    "consistent_learner",
})
ALLOWED_PRIORITIES = frozenset({"low", "medium", "high"})
ALLOWED_ROOT_CAUSES = frozenset({
    "completed",
    "mixed",
    "inactivity",
    "performance",
    "engagement",
    "no_clear_driver",
})

BASE_LEARNER_COLUMNS = [
    "student_id",
    "course_id",
    "status",
    "completion_pct",
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
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"{dataset_name} must be a pandas DataFrame")

    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(
            f"{dataset_name} is missing required columns: "
            + ", ".join(missing)
        )


def _coerce_numeric_strict(
    series: pd.Series,
    column: str,
) -> pd.Series:
    converted = pd.to_numeric(series, errors="coerce")
    invalid = series.notna() & converted.isna()

    if invalid.any():
        raise ValueError(f"{column} contains non-numeric values")

    if converted.isna().any():
        raise ValueError(f"{column} contains missing values")

    return converted


def _normalize_learner_output(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize learner records to the published frontend contract."""
    _require_columns(frame, LEARNER_COLUMNS, "learner analytics")

    output = frame[LEARNER_COLUMNS].copy()

    for column in [
        "student_id",
        "course_id",
        "status",
        "segment",
        "priority",
        "action",
        "root_cause",
    ]:
        output[column] = output[column].astype("string").str.strip()

    # Reuse canonical pipeline validation for the fields owned by pipeline.
    validate_student_course_table(
        output[BASE_LEARNER_COLUMNS].copy()
    )

    output["status"] = (
        output["status"]
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    output["completion_pct"] = _coerce_numeric_strict(
        output["completion_pct"],
        "completion_pct",
    ).round(2)

    if not output["completion_pct"].between(0, 100).all():
        raise ValueError(
            "learner analytics completion_pct must be within 0-100"
        )

    for column, allowed in {
        "segment": ALLOWED_SEGMENTS,
        "priority": ALLOWED_PRIORITIES,
        "root_cause": ALLOWED_ROOT_CAUSES,
    }.items():
        invalid = output[column].notna() & ~output[column].isin(allowed)
        if invalid.any():
            values = sorted(output.loc[invalid, column].dropna().unique())
            raise ValueError(
                f"{column} contains unsupported values: {values}"
            )

    if output["action"].isna().any() | output["action"].eq("").any():
        raise ValueError("learner analytics action cannot be empty")

    if (
        output[["student_id", "course_id"]]
        .isna()
        .any()
        .any()
    ):
        raise ValueError("learner analytics identifiers cannot be missing")

    return (
        output.sort_values(
            ["course_id", "student_id"],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def learner_export(frame: pd.DataFrame) -> pd.DataFrame:
    """Return the stable learner-level contract."""
    return _normalize_learner_output(frame)


def course_export(frame: pd.DataFrame) -> pd.DataFrame:
    """Return the stable course-level contract."""
    _require_columns(frame, COURSE_COLUMNS, "course analytics")

    output = frame[COURSE_COLUMNS].copy()
    output["course_id"] = (
        output["course_id"].astype("string").str.strip()
    )

    if output["course_id"].isna().any() | output["course_id"].eq("").any():
        raise ValueError("course analytics course_id cannot be empty")

    integer_columns = [
        "learner_count",
        "completed_count",
        "dropped_count",
        "high_priority_count",
    ]
    percentage_columns = [
        "completion_rate",
        "dropoff_rate",
        "avg_completion_pct",
        "avg_quiz_accuracy",
    ]
    non_negative_numeric_columns = [
        "avg_study_hours",
        "avg_inactivity_days",
    ]

    for column in integer_columns:
        output[column] = _coerce_numeric_strict(output[column], column).astype("int64")

    for column in percentage_columns + non_negative_numeric_columns:
        output[column] = _coerce_numeric_strict(output[column], column).round(2)

    for column in percentage_columns:
        if not output[column].between(0, 100).all():
            raise ValueError(f"{column} must be within the range 0-100")

    non_negative_columns = integer_columns + non_negative_numeric_columns
    if (output[non_negative_columns] < 0).any().any():
        raise ValueError("course analytics numeric values cannot be negative")

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
        raise ValueError("level must be either 'learner' or 'course'")

    output.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(output, index=False)
    return output


def export_contract_metadata(output_path: str | Path) -> Path:
    """Write the published analytics contract metadata as JSON."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(contract_metadata(), indent=2) + "\n",
        encoding="utf-8",
    )
    return output
