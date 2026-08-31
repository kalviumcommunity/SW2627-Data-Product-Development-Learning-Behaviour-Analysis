"""Pipeline integration tests using the current source-data contract."""

from __future__ import annotations

import pandas as pd

from pipeline.pipeline import run_pipeline


def _write_source_files(raw_dir):
    pd.DataFrame(
        {
            "student_id": ["S001", "S002"],
            "course_id": ["C001", "C001"],
            "completion_pct": [100, 50],
            "status": ["completed", "in_progress"],
        }
    ).to_csv(raw_dir / "completion.csv", index=False)

    pd.DataFrame(
        {
            "student_id": ["S001", "S002"],
            "course_id": ["C001", "C001"],
            "enrollment_date": ["2024-01-01", "2024-01-02"],
            "cohort": ["A", "A"],
        }
    ).to_csv(raw_dir / "enrollment.csv", index=False)

    # Timestamp is part of the current session source contract.
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
            "quiz_id": ["Q1", "Q1"],
            "score": [90, 70],
            "attempt": [1, 1],
        }
    ).to_csv(raw_dir / "quiz.csv", index=False)


def test_run_pipeline_creates_processed_student_course_table(
    tmp_path,
    monkeypatch,
):
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()

    _write_source_files(raw_dir)

    monkeypatch.setattr("pipeline.pipeline.BASE_DATA_PATH", raw_dir)
    monkeypatch.setattr("pipeline.pipeline.PROCESSED_PATH", processed_dir)

    result = run_pipeline()

    assert not result.empty
    assert (processed_dir / "student_course.csv").exists()
    assert (processed_dir / "quality_report.csv").exists()


def test_run_pipeline_produces_transformed_metrics(
    tmp_path,
    monkeypatch,
):
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()

    _write_source_files(raw_dir)

    monkeypatch.setattr("pipeline.pipeline.BASE_DATA_PATH", raw_dir)
    monkeypatch.setattr("pipeline.pipeline.PROCESSED_PATH", processed_dir)

    result = run_pipeline()

    assert set(result["student_id"]) == {"S001", "S002"}
    assert set(result["course_id"]) == {"C001"}
    assert "avg_quiz_score" in result.columns
    assert "quiz_attempts" in result.columns


def test_pipeline_does_not_fabricate_session_dates(
    tmp_path,
    monkeypatch,
):
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()

    _write_source_files(raw_dir)
    sessions = pd.read_csv(raw_dir / "sessions.csv")
    sessions = sessions.drop(columns=["session_date"])
    sessions.to_csv(raw_dir / "sessions.csv", index=False)

    monkeypatch.setattr("pipeline.pipeline.BASE_DATA_PATH", raw_dir)
    monkeypatch.setattr("pipeline.pipeline.PROCESSED_PATH", processed_dir)

    try:
        run_pipeline()
    except ValueError as exc:
        assert "missing start-time field" in str(exc)
    else:
        raise AssertionError(
            "Pipeline should reject session data without a real timestamp"
        )
