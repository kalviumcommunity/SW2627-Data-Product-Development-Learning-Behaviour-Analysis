"""Integration tests for the dashboard analytics data contract."""

from __future__ import annotations

import pandas as pd

from app.services.analytics_service import AnalyticsService


def _write_dataset(path: Path, filename: str, content: str) -> None:
    (path / filename).write_text(content, encoding="utf-8")


def test_analytics_service_load_normalizes_quiz_schema(tmp_path):
    data_path = tmp_path / "raw"
    data_path.mkdir()

    _write_dataset(
        data_path,
        "completion.csv",
        """student_id,course_id,completion_pct,status
S1,C1,85,completed
S2,C1,60,in_progress
""",
    )

    _write_dataset(
        data_path,
        "enrollment.csv",
        """student_id,course_id,enrollment_date,cohort
S1,C1,2024-01-01,A
S2,C1,2024-01-02,A
""",
    )

    _write_dataset(
        data_path,
        "quiz.csv",
        """student_id,course_id,quiz_id,score,attempt
S1,C1,Q1,80,1
S1,C1,Q1,90,2
S2,C1,Q1,70,1
""",
    )

    _write_dataset(
        data_path,
        "sessions.csv",
        """student_id,course_id,session_date,duration_minutes
S1,C1,2024-01-05,40
S1,C1,2024-01-07,35
S2,C1,2024-01-06,20
""",
    )

    dashboard = AnalyticsService(data_path).load()
    quiz = dashboard.raw["quiz"]

    assert {"student_id", "course_id", "score_pct", "attempt_number"} <= set(
        quiz.columns
    )
    assert quiz["score_pct"].tolist() == [80, 90, 70]
    assert quiz["attempt_number"].tolist() == [1, 2, 1]


def test_analytics_service_kpis_work_with_current_quiz_schema(tmp_path):
    data_path = tmp_path / "raw"
    data_path.mkdir()

    _write_dataset(
        data_path,
        "completion.csv",
        """student_id,course_id,completion_pct,status
S1,C1,100,completed
S2,C1,60,in_progress
""",
    )

    _write_dataset(
        data_path,
        "enrollment.csv",
        """student_id,course_id,enrollment_date,cohort
S1,C1,2024-01-01,A
S2,C1,2024-01-02,A
""",
    )

    _write_dataset(
        data_path,
        "quiz.csv",
        """student_id,course_id,quiz_id,score,attempt
S1,C1,Q1,80,1
S1,C1,Q1,100,2
S2,C1,Q1,70,1
""",
    )

    _write_dataset(
        data_path,
        "sessions.csv",
        """student_id,course_id,session_date,duration_minutes
S1,C1,2024-01-05,40
S1,C1,2024-01-07,35
S2,C1,2024-01-06,20
""",
    )

    service = AnalyticsService(data_path)
    dashboard = service.load()

    kpis = service.kpis(dashboard)

    assert kpis["active_students"] == 2
    assert kpis["average_quiz_score"] == 83.33333333333334
