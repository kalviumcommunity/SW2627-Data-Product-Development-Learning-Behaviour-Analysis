"""Tests for ingestion and end-to-end pipeline behavior."""

from pathlib import Path

import pandas as pd
import pytest

from pipeline.ingest import load_all_data
from pipeline.pipeline import run_pipeline


def _write_source_files(raw_dir: Path) -> None:
    pd.DataFrame(
        {
            "student_id": ["S001", "S002"],
            "course_id": ["C001", "C001"],
            "completion_pct": [80, 100],
            "status": ["in_progress", "completed"],
        }
    ).to_csv(raw_dir / "completion.csv", index=False)

    pd.DataFrame(
        {
            "student_id": ["S001", "S002"],
            "course_id": ["C001", "C001"],
            "attempt_number": [1, 1],
            "score_pct": [75, 92],
        }
    ).to_csv(raw_dir / "quiz.csv", index=False)

    pd.DataFrame(
        {
            "student_id": ["S001", "S002"],
            "course_id": ["C001", "C001"],
            "session_date": ["2024-01-05", "2024-01-06"],
            "duration_minutes": [60, 45],
        }
    ).to_csv(raw_dir / "sessions.csv", index=False)

    pd.DataFrame(
        {
            "student_id": ["S001", "S002"],
            "course_id": ["C001", "C001"],
            "enrollment_date": ["2024-08-01", "2024-08-01"],
            "cohort": ["A", "A"],
        }
    ).to_csv(raw_dir / "enrollment.csv", index=False)


def test_load_all_data_reads_all_mvp_sources(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(
        "LEARNLENS_DATA_SOURCE",
        "csv",
    )

    # Reload configuration-dependent ingestion module in an isolated process
    # isn't necessary when this suite imports the function late through the
    # module attribute; patch the module's source mode directly.
    import pipeline.ingest as ingest_module

    monkeypatch.setattr(
        ingest_module,
        "DATA_SOURCE_MODE",
        "csv",
    )

    _write_source_files(tmp_path)

    data = load_all_data(tmp_path)

    assert set(data) == {
        "completion",
        "quiz",
        "sessions",
        "enrollment",
    }
    assert all(len(frame) == 2 for frame in data.values())


def test_load_all_data_raises_for_missing_source(
    tmp_path,
    monkeypatch,
):
    import pipeline.ingest as ingest_module

    monkeypatch.setattr(
        ingest_module,
        "DATA_SOURCE_MODE",
        "csv",
    )

    with pytest.raises(
        FileNotFoundError,
        match="Input file not found",
    ):
        load_all_data(tmp_path)


def test_run_pipeline_creates_processed_student_course_table(
    tmp_path,
    monkeypatch,
):
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    _write_source_files(raw_dir)

    import pipeline.pipeline as pipeline_module

    monkeypatch.setattr(
        pipeline_module,
        "BASE_DATA_PATH",
        raw_dir,
    )
    monkeypatch.setattr(
        pipeline_module,
        "PROCESSED_PATH",
        processed_dir,
    )
    monkeypatch.setattr(
        pipeline_module,
        "DATA_SOURCE_MODE",
        "csv",
    )

    import pipeline.ingest as ingest_module

    monkeypatch.setattr(
        ingest_module,
        "DATA_SOURCE_MODE",
        "csv",
    )

    result = run_pipeline(raw_dir)
    output_path = processed_dir / "student_course.csv"

    assert output_path.exists()
    assert len(result) == 2


def test_run_pipeline_produces_transformed_metrics(
    tmp_path,
    monkeypatch,
):
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    _write_source_files(raw_dir)

    import pipeline.pipeline as pipeline_module
    import pipeline.ingest as ingest_module

    monkeypatch.setattr(
        pipeline_module,
        "BASE_DATA_PATH",
        raw_dir,
    )
    monkeypatch.setattr(
        pipeline_module,
        "PROCESSED_PATH",
        processed_dir,
    )
    monkeypatch.setattr(
        pipeline_module,
        "DATA_SOURCE_MODE",
        "csv",
    )
    monkeypatch.setattr(
        ingest_module,
        "DATA_SOURCE_MODE",
        "csv",
    )

    result = run_pipeline(raw_dir)

    assert "total_duration" in result.columns
    assert "session_count" in result.columns
    assert "avg_quiz_score" in result.columns
    assert "quiz_attempts" in result.columns
