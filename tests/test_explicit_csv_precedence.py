"""Regression test for explicit CSV source precedence."""

from pathlib import Path

import pandas as pd

import pipeline.ingest as ingest


def test_explicit_csv_path_overrides_default_source_mode(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        ingest,
        "DATA_SOURCE_MODE",
        "synthetic",
    )

    pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "completion_pct": [80],
            "status": ["completed"],
        }
    ).to_csv(
        tmp_path / "completion.csv",
        index=False,
    )

    pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "enrollment_date": ["2024-01-01"],
            "cohort": ["A"],
        }
    ).to_csv(
        tmp_path / "enrollment.csv",
        index=False,
    )

    pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "session_date": ["2024-01-05"],
            "duration_minutes": [30],
        }
    ).to_csv(
        tmp_path / "sessions.csv",
        index=False,
    )

    pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "score": [90],
            "attempt": [1],
        }
    ).to_csv(
        tmp_path / "quiz.csv",
        index=False,
    )

    data = ingest.load_all_data(
        Path(tmp_path)
    )

    assert data["completion"].loc[0, "completion_pct"] == 80
    assert data["quiz"].loc[0, "score"] == 90
    assert data["sessions"].loc[0, "duration_minutes"] == 30
