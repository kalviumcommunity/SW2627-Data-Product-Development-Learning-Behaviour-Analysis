"""Regression tests for the schema/artifact production hardening PR."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from pipeline.quality import (
    REQUIRED_SCHEMAS,
    generate_quality_report,
)
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


def _student_course() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "completion_pct": [80],
            "quiz_accuracy": [75],
        }
    )


def _minimal_source() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
        }
    )


def _production_sources() -> dict[str, pd.DataFrame]:
    return {
        name: _minimal_source()
        for name in SOURCE_DATASET_NAMES
    }


def test_generate_quality_report_keeps_public_schema():
    report = generate_quality_report(
        {
            "completion": _minimal_source(),
        }
    )

    assert list(report.columns) == [
        "dataset",
        "row_count",
        "missing_values",
        "duplicate_rows",
        "invalid_id_rows",
        "valid",
    ]


def test_schema_manifest_matches_validation_contract():
    manifest = schema_manifest()

    assert manifest["version"] == PIPELINE_SCHEMA_VERSION
    assert tuple(manifest["datasets"]) == (
        SOURCE_DATASET_NAMES
    )

    for name in SOURCE_DATASET_NAMES:
        assert tuple(
            manifest["datasets"][name]["required_columns"]
        ) == tuple(
            REQUIRED_SCHEMAS[name]
        )


def test_strict_gate_requires_all_sources():
    sources = _production_sources()
    sources.pop("enrollment")

    with pytest.raises(
        ValueError,
        match="missing source dataset",
    ):
        validate_pipeline_output(
            sources,
            _student_course(),
            require_all_sources=True,
        )


def test_strict_gate_rejects_unknown_source():
    sources = _production_sources()
    sources["unexpected"] = _minimal_source()

    with pytest.raises(
        ValueError,
        match="unknown source dataset",
    ):
        validate_pipeline_output(
            sources,
            _student_course(),
            require_all_sources=True,
        )


def test_non_dataframe_source_is_type_error():
    with pytest.raises(
        TypeError,
        match="pandas DataFrame",
    ):
        validate_pipeline_output(
            {"completion": []},
            _student_course(),
        )


def test_quality_report_writer_creates_parent_directories(
    tmp_path: Path,
):
    report = pd.DataFrame(
        {
            "dataset": ["completion"],
            "row_count": [1],
            "missing_values": [0],
            "duplicate_rows": [0],
            "invalid_id_rows": [0],
            "valid": [True],
        }
    )

    output = write_quality_report(
        report,
        tmp_path / "nested" / "quality_report.csv",
    )

    assert output.exists()
    assert pd.read_csv(output)["valid"].tolist() == [True]
    assert not list(
        output.parent.glob("*.tmp")
    )


def test_manifest_contains_schema_version_and_row_count(
    tmp_path: Path,
):
    output = write_pipeline_manifest(
        tmp_path / "pipeline_manifest.json",
        row_count=42,
        quality_report_path="quality_report.csv",
        student_course_path="student_course.csv",
    )

    payload = json.loads(
        output.read_text(encoding="utf-8")
    )

    assert payload["schema_version"] == (
        PIPELINE_SCHEMA_VERSION
    )
    assert payload["row_count"] == 42
    assert payload["schema"]["version"] == (
        PIPELINE_SCHEMA_VERSION
    )
