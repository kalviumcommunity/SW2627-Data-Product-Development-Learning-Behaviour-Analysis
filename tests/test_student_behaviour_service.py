import pandas as pd

from app.services.analytics_service import (
    ALL_COURSES,
    AnalyticsService,
    DashboardData,
)


def fixture_data():
    return DashboardData(
        raw={
            "completion": pd.DataFrame(
                {
                    "student_id": ["S1", "S2", "S3"],
                    "course_id": ["C1", "C1", "C2"],
                    "completion_pct": [100, 50, 100],
                    "status": ["completed", "in_progress", "completed"],
                }
            ),
            "quiz": pd.DataFrame(
                {
                    "student_id": ["S1", "S1", "S2", "S3"],
                    "course_id": ["C1", "C1", "C1", "C2"],
                    "attempt_number": [1, 2, 1, 1],
                    "score_pct": [80, 90, 70, 95],
                }
            ),
            "sessions": pd.DataFrame(
                {
                    "student_id": ["S1", "S1", "S2", "S3"],
                    "course_id": ["C1", "C1", "C1", "C2"],
                    "duration_minutes": [30, 45, 20, 60],
                }
            ),
            "enrollment": pd.DataFrame(
                {
                    "student_id": ["S1", "S2", "S3"],
                    "course_id": ["C1", "C1", "C2"],
                }
            ),
        }
    )


def test_behaviour_summary_uses_current_schema():
    service = AnalyticsService()
    summary = service.behaviour_summary(fixture_data())

    assert summary["learner_count"] == 3
    assert summary["avg_quiz_attempts"] > 0
    assert summary["avg_study_time_hours"] > 0


def test_behaviour_filter_uses_canonical_population():
    service = AnalyticsService()

    filtered = service.filter_data(
        fixture_data(),
        course=ALL_COURSES,
        status="Completed",
    )

    assert set(filtered.raw["completion"]["student_id"]) == {"S1", "S3"}
    assert set(filtered.raw["quiz"]["student_id"]) == {"S1", "S3"}
    assert set(filtered.raw["sessions"]["student_id"]) == {"S1", "S3"}


def test_behaviour_by_status_returns_expected_columns():
    service = AnalyticsService()
    summary = service.behaviour_by_status(fixture_data())

    assert {
        "status",
        "learners",
        "avg_completion_pct",
        "avg_quiz_score",
        "avg_quiz_attempts",
        "avg_study_hours",
        "avg_sessions",
    }.issubset(summary.columns)
