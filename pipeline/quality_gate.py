"""Production data-quality gate for pipeline outputs.

This module is the enforcement boundary around the canonical validators in
``pipeline.quality``. It does not duplicate data-quality rules.
"""

from __future__ import annotations

from pathlib import Path
from collections.abc import Mapping

import pandas as pd

from pipeline.quality import generate_quality_report, validate_student_course_table


def validate_pipeline_output(
    source_datasets: Mapping[str, pd.DataFrame],
    student_course_df: pd.DataFrame,
) -> pd.DataFrame:
    """Validate pipeline inputs and the final student-course output."""
    if not isinstance(source_datasets, Mapping):
        raise TypeError(
            "source_datasets must be a mapping of dataset names to pandas DataFrames"
        )

    report = generate_quality_report(source_datasets)

    invalid_datasets = report.loc[~report["valid"], "dataset"].astype(str).tolist()
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
    """Persist a quality report to CSV and return the written path."""
    if not isinstance(report, pd.DataFrame):
        raise TypeError("report must be a pandas DataFrame")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(output, index=False)
    return output
