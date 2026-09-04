"""Production quality gate and atomic production artifact writers."""

from __future__ import annotations

from collections.abc import Mapping
import json
import os
from pathlib import Path
import tempfile

import pandas as pd

from pipeline.quality import (
    generate_quality_report,
    validate_student_course_table,
)
from pipeline.schema import (
    PIPELINE_SCHEMA_VERSION,
    SOURCE_DATASET_NAMES,
    schema_manifest,
)


def validate_pipeline_output(
    source_datasets: Mapping[str, pd.DataFrame],
    student_course_df: pd.DataFrame,
    *,
    require_all_sources: bool = False,
) -> pd.DataFrame:
    """Validate source datasets and the final student-course handoff."""
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
        missing = sorted(
            set(SOURCE_DATASET_NAMES) - set(source_datasets)
        )
        if missing:
            raise ValueError(
                "data-quality checks failed: missing source "
                "dataset(s): " + ", ".join(missing)
            )

        unknown = sorted(
            set(source_datasets) - set(SOURCE_DATASET_NAMES)
        )
        if unknown:
            raise ValueError(
                "data-quality checks failed: unknown source "
                "dataset(s): " + ", ".join(unknown)
            )

    report = generate_quality_report(
        source_datasets
    )

    invalid = (
        report.loc[~report["valid"], "dataset"]
        .astype(str)
        .tolist()
    )
    if invalid:
        raise ValueError(
            "data-quality checks failed for source dataset(s): "
            + ", ".join(invalid)
        )

    validate_student_course_table(
        student_course_df
    )
    return report


def _atomic_csv(
    frame: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    """Atomically write a dataframe to CSV.

    The file is first written to a temporary file in the destination
    directory. The temporary file is flushed and synced before being
    atomically renamed into place.

    Using the original mkstemp file descriptor avoids Windows-specific
    descriptor/handle issues caused by reopening the temporary path.
    """
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(
            "frame must be a pandas DataFrame"
        )

    output = Path(output_path)
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fd, temporary = tempfile.mkstemp(
        prefix=f".{output.name}.",
        suffix=".tmp",
        dir=output.parent,
        text=True,
    )

    try:
        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:
            frame.to_csv(
                handle,
                index=False,
            )
            handle.flush()
            os.fsync(
                handle.fileno()
            )

        os.replace(
            temporary,
            output,
        )

    except Exception:
        try:
            os.unlink(
                temporary
            )
        except FileNotFoundError:
            pass
        raise

    return output


def _atomic_text(
    content: str,
    output_path: str | Path,
) -> Path:
    """Atomically write UTF-8 text to a file."""
    output = Path(output_path)
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fd, temporary = tempfile.mkstemp(
        prefix=f".{output.name}.",
        suffix=".tmp",
        dir=output.parent,
        text=True,
    )

    try:
        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(
                handle.fileno()
            )

        os.replace(
            temporary,
            output,
        )

    except Exception:
        try:
            os.unlink(
                temporary
            )
        except FileNotFoundError:
            pass
        raise

    return output


def write_quality_report(
    report: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    """Atomically persist the quality report."""
    return _atomic_csv(
        report,
        output_path,
    )


def write_pipeline_manifest(
    output_path: str | Path,
    *,
    row_count: int,
    quality_report_path: str | Path,
    student_course_path: str | Path,
) -> Path:
    """Persist reproducibility metadata for the pipeline run."""
    if row_count < 0:
        raise ValueError(
            "row_count cannot be negative"
        )

    payload = {
        "schema_version": PIPELINE_SCHEMA_VERSION,
        "row_count": int(row_count),
        "quality_report": str(
            quality_report_path
        ),
        "student_course": str(
            student_course_path
        ),
        "schema": schema_manifest(),
    }

    return _atomic_text(
        json.dumps(
            payload,
            indent=2,
        )
        + "\n",
        output_path,
    )
