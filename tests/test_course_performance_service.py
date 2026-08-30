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
                    "student_id": ["S1", "S2", "S3", "S4"],
                    "course_id": ["C1", "C1", "C2", "C2"],
                    "completion_pct": [100, 50, 100, 40],
                    "status": [
                        "completed",
                        "in_progress",
                        "completed",
                        "dropped",
                    ],
                }
            ),
            "quiz": pd.DataFrame(
                {
                    "student_id": ["S1", "S2", "S3", "S4"],
                    "course_id": ["C1", "C1", "C2", "C2"],
                    "score_pct": [90, 60, 85, 40],
                    "attempt_number": [1, 1, 2, 1],
                }
            ),
            "sessions": pd.DataFrame(
                {
                    "student_id": ["S1", "S1", "S2", "S3", "S4"],
                    "course_id": ["C1", "C1", "C1", "C2", "C2"],
                    "duration_minutes": [30, 60, 20, 90, 15],
                }
            ),
        }
    )


def test_course_performance_returns_one_row_per_course():
    result = AnalyticsService().course_performance(fixture_data())

    assert set(result["course_id"]) == {"C1", "C2"}
    assert len(result) == 2


def test_course_completion_and_dropout_rates():
    result = AnalyticsService().course_performance(fixture_data())

    c1 = result.loc[result["course_id"] == "C1"].iloc[0]
    c2 = result.loc[result["course_id"] == "C2"].iloc[0]

    assert c1["completion_rate"] == 50.0
    assert c2["completion_rate"] == 50.0
    assert c1["dropout_rate"] == 0.0
    assert c2["dropout_rate"] == 50.0


def test_course_average_quiz_score():
    result = AnalyticsService().course_performance(fixture_data())

    c1 = result.loc[result["course_id"] == "C1"].iloc[0]
    c2 = result.loc[result["course_id"] == "C2"].iloc[0]

    assert c1["avg_quiz_score"] == 75.0
    assert c2["avg_quiz_score"] == 62.5


def test_course_study_hours():
    result = AnalyticsService().course_performance(fixture_data())

    c1 = result.loc[result["course_id"] == "C1"].iloc[0]
    c2 = result.loc[result["course_id"] == "C2"].iloc[0]

    # 30 + 60 + 20 = 110 minutes = 1.83 hours.
    assert c1["study_hours"] == 1.83
    assert c2["study_hours"] == 1.75


def test_status_filter_uses_canonical_population():
    service = AnalyticsService()

    filtered = service.filter_data(
        fixture_data(),
        course=ALL_COURSES,
        status="dropped",
    )

    assert set(filtered.raw["completion"]["student_id"]) == {"S4"}
    assert set(filtered.raw["quiz"]["student_id"]) == {"S4"}
    assert set(filtered.raw["sessions"]["student_id"]) == {"S4"}


def test_course_performance_does_not_require_attempt_number():
    result = AnalyticsService().course_performance(fixture_data())

    assert not result.empty


def test_empty_completion_returns_empty_result():
    data = fixture_data()
    data.raw["completion"] = data.raw["completion"].iloc[0:0].copy()

    result = AnalyticsService().course_performance(data)

    assert result.empty


def test_duplicate_completion_grain_is_rejected():
    data = fixture_data()
    data.raw["completion"] = pd.concat(
        [
            data.raw["completion"],
            data.raw["completion"].iloc[[0]],
        ],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="one row per student-course pair",
    ):
        AnalyticsService().course_performance(data)


def test_course_performance_accepts_canonical_quiz_schema():
    result = AnalyticsService().course_performance(fixture_data())
    assert not result.empty
