"""Canonical schema metadata shared by the production pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


PIPELINE_SCHEMA_VERSION: Final[str] = "1.0"

SOURCE_DATASET_NAMES: Final[tuple[str, ...]] = (
    "completion",
    "enrollment",
    "sessions",
    "quiz",
)


@dataclass(frozen=True)
class DatasetSchema:
    """Schema metadata for one source dataset."""

    name: str
    required_columns: tuple[str, ...]
    grain: str


SOURCE_SCHEMAS: Final[dict[str, DatasetSchema]] = {
    "completion": DatasetSchema(
        name="completion",
        required_columns=(
            "student_id",
            "course_id",
            "completion_pct",
            "status",
        ),
        grain="one row per student-course",
    ),
    "enrollment": DatasetSchema(
        name="enrollment",
        required_columns=(
            "student_id",
            "course_id",
            "enrollment_date",
            "cohort",
        ),
        grain="one row per student-course",
    ),
    "sessions": DatasetSchema(
        name="sessions",
        required_columns=(
            "student_id",
            "course_id",
            "duration_minutes",
            "start_time",
        ),
        grain="one row per session",
    ),
    "quiz": DatasetSchema(
        name="quiz",
        required_columns=(
            "student_id",
            "course_id",
            "attempt_number",
            "score_pct",
        ),
        grain="one row per quiz attempt",
    ),
}


def schema_manifest() -> dict[str, object]:
    """Return a JSON-serializable pipeline schema manifest."""
    return {
        "version": PIPELINE_SCHEMA_VERSION,
        "datasets": {
            name: {
                "required_columns": list(schema.required_columns),
                "grain": schema.grain,
            }
            for name, schema in SOURCE_SCHEMAS.items()
        },
    }
