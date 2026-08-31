"""End-to-end smoke tests for the default synthetic pipeline."""

from __future__ import annotations

import json

import pandas as pd

import pipeline.pipeline as pipeline_module
from pipeline.synthetic_data import SyntheticDataConfig, generate_synthetic_datasets


def test_synthetic_generator_has_stable_contract():
    data = generate_synthetic_datasets(
        SyntheticDataConfig(
            seed=42,
            students=25,
            courses=4,
            days=30,
        )
    )

    assert set(data) == {
        "completion",
        "enrollment",
        "sessions",
        "quiz",
    }

    assert not data["completion"].empty
    assert not data["enrollment"].empty
    assert not data["sessions"].empty
    assert not data["quiz"].empty


def test_default_pipeline_runs_without_raw_csv_files(
    tmp_path,
    monkeypatch,
):
    # Force synthetic mode for this test regardless of the developer's shell
    # environment.
    monkeypatch.setattr(
        "pipeline.ingest.DATA_SOURCE_MODE",
        "synthetic",
    )
    monkeypatch.setattr(
        pipeline_module,
        "DATA_SOURCE_MODE",
        "synthetic",
    )
    monkeypatch.setattr(
        pipeline_module,
        "PROCESSED_PATH",
        tmp_path / "processed",
    )

    result = pipeline_module.run_pipeline()

    output = tmp_path / "processed"

    assert not result.empty
    assert len(result) > 0
    assert (output / "student_course.csv").is_file()
    assert (output / "quality_report.csv").is_file()
    assert (output / "pipeline_manifest.json").is_file()


def test_default_pipeline_manifest_describes_generated_run(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "pipeline.ingest.DATA_SOURCE_MODE",
        "synthetic",
    )
    monkeypatch.setattr(
        pipeline_module,
        "DATA_SOURCE_MODE",
        "synthetic",
    )
    monkeypatch.setattr(
        pipeline_module,
        "PROCESSED_PATH",
        tmp_path / "processed",
    )

    result = pipeline_module.run_pipeline()

    manifest_path = (
        tmp_path
        / "processed"
        / "pipeline_manifest.json"
    )

    payload = json.loads(
        manifest_path.read_text(
            encoding="utf-8"
        )
    )

    saved = pd.read_csv(
        tmp_path
        / "processed"
        / "student_course.csv"
    )

    assert payload["row_count"] == len(result)
    assert payload["row_count"] == len(saved)
    assert payload["schema_version"]
    assert payload["student_course"].endswith(
        "student_course.csv"
    )


def test_pipeline_output_is_valid_for_downstream_dashboard(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "pipeline.ingest.DATA_SOURCE_MODE",
        "synthetic",
    )
    monkeypatch.setattr(
        pipeline_module,
        "DATA_SOURCE_MODE",
        "synthetic",
    )
    monkeypatch.setattr(
        pipeline_module,
        "PROCESSED_PATH",
        tmp_path / "processed",
    )

    result = pipeline_module.run_pipeline()

    required = {
        "student_id",
        "course_id",
        "completion_pct",
        "status",
        "total_duration",
        "session_count",
        "avg_quiz_score",
        "quiz_attempts",
    }

    assert required.issubset(result.columns)
    assert not result.duplicated(
        ["student_id", "course_id"]
    ).any()
