"""Regression tests for the hardened pipeline contract."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from pipeline.quality_gate import (
    validate_pipeline_output,
    write_pipeline_manifest,
    write_quality_report,
)
from pipeline.schema import (
    PIPELINE_SCHEMA_VERSION,
    SOURCE_DATASET_NAMES,
    schema_manifest,
)
from pipeline.validate import REQUIRED_SCHEMAS


def source_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
        }
    )


def student_course() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "completion_pct": [80],
            "quiz_accuracy": [75],
        }
    )


def test_schema_metadata_is_the_validation_source():
    assert tuple(REQUIRED_SCHEMAS) == SOURCE_DATASET_NAMES

    manifest = schema_manifest()
    assert manifest["version"] == PIPELINE_SCHEMA_VERSION

    for name in SOURCE_DATASET_NAMES:
        assert (
            tuple(
                manifest["datasets"][name]["required_columns"]
            )
            == tuple(REQUIRED_SCHEMAS[name])
        )


def test_strict_quality_gate_requires_all_four_sources():
    data = {
        name: source_frame()
        for name in SOURCE_DATASET_NAMES
    }
    data.pop("quiz")

    with pytest.raises(
        ValueError,
        match="missing source dataset",
    ):
        validate_pipeline_output(
            data,
            student_course(),
            require_all_sources=True,
        )


def test_strict_quality_gate_rejects_unknown_sources():
    data = {
        name: source_frame()
        for name in SOURCE_DATASET_NAMES
    }
    data["unexpected"] = source_frame()

    with pytest.raises(
        ValueError,
        match="unknown source dataset",
    ):
        validate_pipeline_output(
            data,
            student_course(),
            require_all_sources=True,
        )


def test_non_dataframe_source_gets_type_error():
    with pytest.raises(
        TypeError,
        match="pandas DataFrame",
    ):
        validate_pipeline_output(
            {"completion": []},
            student_course(),
        )


def test_quality_report_schema_remains_backward_compatible():
    report = write_quality_report

    frame = pd.DataFrame(
        {
            "dataset": ["completion"],
            "row_count": [1],
            "missing_values": [0],
            "duplicate_rows": [0],
            "invalid_id_rows": [0],
            "valid": [True],
        }
    )

    # This test intentionally checks the existing public report shape.
    output = __import__("tempfile").NamedTemporaryFile(
        suffix=".csv",
        delete=False,
    )
    output.close()

    try:
        path = report(frame, output.name)
        saved = pd.read_csv(path)

        assert list(saved.columns) == [
            "dataset",
            "row_count",
            "missing_values",
            "duplicate_rows",
            "invalid_id_rows",
            "valid",
        ]
    finally:
        import os
        os.unlink(output.name)


def test_manifest_is_json_and_versioned(tmp_path):
    target = tmp_path / "pipeline_manifest.json"

    write_pipeline_manifest(
        target,
        row_count=10,
        quality_report_path=tmp_path / "quality_report.csv",
        student_course_path=tmp_path / "student_course.csv",
    )

    payload = json.loads(
        target.read_text(encoding="utf-8")
    )

    assert payload["schema_version"] == PIPELINE_SCHEMA_VERSION
    assert payload["row_count"] == 10
    assert payload["schema"]["version"] == PIPELINE_SCHEMA_VERSION
