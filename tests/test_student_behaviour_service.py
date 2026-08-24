import pandas as pd
import pytest

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
                    "duration_minutes": [30, 90, 20, 60],
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


def test_study_time_is_aggregated_per_student_course():
    service = AnalyticsService()
    summary = service.behaviour_summary(fixture_data())

    # S1/C1 = 120m, S2/C1 = 20m, S3/C2 = 60m.
    # Mean = 66.67m = 1.11h.
    assert summary["avg_study_time_hours"] == 1.11
    assert summary["avg_sessions"] == pytest.approx(1.33, abs=0.01)


def test_quiz_attempts_are_calculated():
    service = AnalyticsService()
    summary = service.behaviour_summary(fixture_data())

    assert summary["avg_quiz_attempts"] == 1.25


def test_completion_rate_is_calculated():
    service = AnalyticsService()
    summary = service.behaviour_summary(fixture_data())

    assert summary["completion_rate"] == pytest.approx(66.7, abs=0.1)


def test_status_filter_uses_canonical_population():
    service = AnalyticsService()

    filtered = service.filter_data(
        fixture_data(),
        course=ALL_COURSES,
        status="Completed",
    )

    assert set(filtered.raw["completion"]["student_id"]) == {"S1", "S3"}
    assert set(filtered.raw["quiz"]["student_id"]) == {"S1", "S3"}
    assert set(filtered.raw["sessions"]["student_id"]) == {"S1", "S3"}


def test_duplicate_completion_grain_is_rejected():
    data = fixture_data()
    data.raw["completion"] = pd.concat(
        [data.raw["completion"], data.raw["completion"].iloc[[0]]],
        ignore_index=True,
    )

    service = AnalyticsService()

    with pytest.raises(ValueError, match="one row per student-course pair"):
        service.behaviour_summary(data)


def test_empty_completion_returns_zero_metrics():
    data = fixture_data()
    data.raw["completion"] = data.raw["completion"].iloc[0:0].copy()

    summary = AnalyticsService().behaviour_summary(data)

    assert summary["avg_study_time_hours"] == 0.0
    assert summary["avg_sessions"] == 0.0
    assert summary["avg_quiz_attempts"] == 0.0
    assert summary["completion_rate"] == 0.0


def test_empty_sessions_returns_zero_study_metrics():
    data = fixture_data()
    data.raw["sessions"] = data.raw["sessions"].iloc[0:0].copy()

    summary = AnalyticsService().behaviour_summary(data)

    assert summary["avg_study_time_hours"] == 0.0
    assert summary["avg_sessions"] == 0.0


def test_empty_quiz_returns_zero_attempt_metric():
    data = fixture_data()
    data.raw["quiz"] = data.raw["quiz"].iloc[0:0].copy()

    summary = AnalyticsService().behaviour_summary(data)

    assert summary["avg_quiz_attempts"] == 0.0


def test_behaviour_by_status_has_expected_columns():
    summary = AnalyticsService().behaviour_by_status(fixture_data())

    assert {
        "status",
        "learners",
        "avg_completion_pct",
        "avg_quiz_score",
        "avg_quiz_attempts",
        "avg_study_hours",
        "avg_sessions",
    }.issubset(summary.columns)
