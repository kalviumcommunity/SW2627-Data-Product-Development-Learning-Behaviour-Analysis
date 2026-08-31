import pandas as pd

from app.services.analytics_service import (
    ALL_COURSES,
    ALL_SEGMENTS,
    ALL_STATUSES,
    AnalyticsService,
    DashboardData,
)


def _dashboard() -> DashboardData:
    completion = pd.DataFrame(
        {
            "student_id": ["S1", "S2", "S3"],
            "course_id": ["C1", "C1", "C2"],
            "completion_pct": [100, 50, 100],
            "status": ["completed", "in_progress", "completed"],
            "enrollment_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        }
    )
    quiz = pd.DataFrame(
        {
            "student_id": ["S1", "S2", "S3"],
            "course_id": ["C1", "C1", "C2"],
            "score_pct": [90, 60, 95],
        }
    )
    sessions = pd.DataFrame(
        {
            "student_id": ["S1", "S2", "S3"],
            "course_id": ["C1", "C1", "C2"],
            "duration_minutes": [60, 30, 45],
        }
    )
    enrollment = pd.DataFrame(
        {
            "student_id": ["S1", "S2", "S3"],
            "course_id": ["C1", "C1", "C2"],
            "enrollment_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "cohort": ["A", "A", "B"],
        }
    )
    features = pd.DataFrame(
        {
            "student_id": ["S1", "S2", "S3"],
            "course_id": ["C1", "C1", "C2"],
            "cohort": ["A", "A", "B"],
            "total_study_hours": [1.0, 0.5, 0.75],
            "avg_session_length": [60.0, 30.0, 45.0],
            "quiz_accuracy": [90.0, 60.0, 95.0],
            "quiz_frequency": [1.0, 1.0, 1.0],
            "active_days": [1.0, 1.0, 1.0],
            "learning_streak": [1.0, 1.0, 1.0],
            "days_since_last_activity": [1.0, 2.0, 1.0],
            "weekly_sessions": [1.0, 1.0, 1.0],
            "completion_pct": [100.0, 50.0, 100.0],
            "status": ["completed", "in_progress", "completed"],
        }
    )
    segments = pd.DataFrame(
        {
            "student_id": ["S1", "S2", "S3"],
            "course_id": ["C1", "C1", "C2"],
            "segment": ["completed", "low_engagement", "completed"],
        }
    )
    return DashboardData(
        raw={
            "completion": completion,
            "quiz": quiz,
            "sessions": sessions,
            "enrollment": enrollment,
        },
        features=features,
        segments=segments,
    )


def test_filter_by_course():
    filtered = AnalyticsService.filter_data(
        _dashboard(),
        course="C2",
        segment=ALL_SEGMENTS,
        status=ALL_STATUSES,
    )

    assert filtered.features["student_id"].tolist() == ["S3"]
    assert filtered.raw["completion"]["student_id"].tolist() == ["S3"]


def test_filter_by_status():
    filtered = AnalyticsService.filter_data(
        _dashboard(),
        course=ALL_COURSES,
        segment=ALL_SEGMENTS,
        status="Completed",
    )

    assert set(filtered.features["student_id"]) == {"S1", "S3"}


def test_filter_by_segment():
    filtered = AnalyticsService.filter_data(
        _dashboard(),
        course=ALL_COURSES,
        segment="Silent At-Risk",
        status=ALL_STATUSES,
    )

    # No at-risk learners in this fixture.
    assert filtered.features.empty


def test_filter_by_date():
    filtered = AnalyticsService.filter_data(
        _dashboard(),
        course=ALL_COURSES,
        segment=ALL_SEGMENTS,
        status=ALL_STATUSES,
        selected_date=pd.Timestamp("2024-01-02"),
    )

    assert filtered.raw["completion"]["student_id"].tolist() == ["S2"]
