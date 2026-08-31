"""Regression tests for synthetic/default and explicit CSV ingestion."""

from pathlib import Path

import pandas as pd

from pipeline.ingest import load_all_data


def _write_minimal_sources(path: Path) -> None:
    pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "completion_pct": [80],
            "status": ["completed"],
        }
    ).to_csv(path / "completion.csv", index=False)

    pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "enrollment_date": ["2024-01-01"],
            "cohort": ["A"],
        }
    ).to_csv(path / "enrollment.csv", index=False)

    pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "quiz_id": ["Q1"],
            "score": [80],
            "attempt": [1],
        }
    ).to_csv(path / "quiz.csv", index=False)

    pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "session_date": ["2024-01-05"],
            "duration_minutes": [30],
        }
    ).to_csv(path / "sessions.csv", index=False)


def test_explicit_path_always_uses_csv(tmp_path):
    _write_minimal_sources(tmp_path)

    data = load_all_data(tmp_path)

    assert len(data["completion"]) == 1
    assert data["completion"].loc[0, "completion_pct"] == 80
    assert data["quiz"].loc[0, "score"] == 80
