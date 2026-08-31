"""Production quality-gate enforcement for pipeline outputs."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pandas as pd

from pipeline.quality import (
    generate_quality_report,
    validate_student_course_table,
)

PRODUCTION_SOURCES = frozenset(
    {"completion", "enrollment", "sessions", "quiz"}
)


def validate_pipeline_output(
    source_datasets: Mapping[str, pd.DataFrame],
    student_course_df: pd.DataFrame,
    *,
    require_all_sources: bool = False,
) -> pd.DataFrame:
    """Validate supplied sources and the final analytics handoff.

    ``require_all_sources=True`` is reserved for the real production
    pipeline. Focused callers can validate a subset without being forced to
    construct unrelated datasets.
    """
    if not isinstance(source_datasets, Mapping):
        raise TypeError(
            "source_datasets must be a mapping of dataset names "
            "to pandas DataFrames"
        )

    for name, frame in source_datasets.items():
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(
                f"{name} must be a pandas DataFrame"
            )

    if require_all_sources:
        missing_sources = sorted(
            PRODUCTION_SOURCES - set(source_datasets)
        )
        if missing_sources:
            raise ValueError(
                "data-quality checks failed: missing source "
                "dataset(s): " + ", ".join(missing_sources)
            )

    report = generate_quality_report(source_datasets)

    invalid_datasets = (
        report.loc[~report["valid"], "dataset"]
        .astype(str)
        .tolist()
    )
    if invalid_datasets:
        raise ValueError(
            "data-quality checks failed for source dataset(s): "
            + ", ".join(invalid_datasets)
        )

    validate_student_course_table(student_course_df)
    return report


def write_quality_report(
    report: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    """Persist the canonical quality report to CSV."""
    if not isinstance(report, pd.DataFrame):
        raise TypeError("report must be a pandas DataFrame")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(output, index=False)
    return output
