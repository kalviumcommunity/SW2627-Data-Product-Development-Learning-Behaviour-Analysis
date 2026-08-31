"""Versioned canonical schema metadata for the source pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from pipeline.quality import REQUIRED_SCHEMAS


PIPELINE_SCHEMA_VERSION: Final[str] = "1.0"

SOURCE_DATASET_NAMES: Final[tuple[str, ...]] = (
    "completion",
    "enrollment",
    "sessions",
    "quiz",
)


@dataclass(frozen=True)
class DatasetSchema:
    name: str
    required_columns: tuple[str, ...]
    grain: str


GRAINS = {
    "completion": "one row per student-course",
    "enrollment": "one row per student-course",
    "sessions": "one row per session",
    "quiz": "one row per quiz attempt",
}


SOURCE_SCHEMAS: dict[str, DatasetSchema] = {
    name: DatasetSchema(
        name=name,
        required_columns=tuple(REQUIRED_SCHEMAS[name]),
        grain=GRAINS[name],
    )
    for name in SOURCE_DATASET_NAMES
}


def schema_manifest() -> dict[str, object]:
    return {
        "version": PIPELINE_SCHEMA_VERSION,
        "datasets": {
            name: {
                "required_columns": list(
                    schema.required_columns
                ),
                "grain": schema.grain,
            }
            for name, schema in SOURCE_SCHEMAS.items()
        },
    }
