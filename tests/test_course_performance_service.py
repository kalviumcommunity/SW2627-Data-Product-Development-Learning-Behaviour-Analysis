import pandas as pd
import pytest

from app.services.analytics_service import (
    ALL_COURSES,
    ALL_SEGMENTS,
    ALL_STATUSES,
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
                    "attempt_number": [1, 1, 1, 1],
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


def test_dashboard_data_accepts_optional_features_and_segments():
    features = pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "total_study_hours": [1.5],
        }
    )
    segments = pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "segment": ["completed"],
        }
    )

    dashboard = DashboardData(
        raw={},
        features=features,
        segments=segments,
    )

    assert dashboard.features is features
    assert dashboard.segments is segments


def test_filter_data_preserves_optional_analytics_tables():
    base = fixture_data()

    dashboard = DashboardData(
        raw=base.raw,
        features=pd.DataFrame(
            {
                "student_id": ["S1", "S2", "S3"],
                "course_id": ["C1", "C1", "C2"],
                "total_study_hours": [1.5, 1.0, 2.0],
            }
        ),
        segments=pd.DataFrame(
            {
                "student_id": ["S1", "S2", "S3"],
                "course_id": ["C1", "C1", "C2"],
                "segment": [
                    "completed",
                    "low_engagement",
                    "completed",
                ],
            }
        ),
    )

    filtered = AnalyticsService.filter_data(
        dashboard,
        course="C1",
        status="completed",
    )

    assert filtered.features is not None
    assert filtered.features["student_id"].tolist() == ["S1"]
    assert filtered.segments is not None
    assert filtered.segments["student_id"].tolist() == ["S1"]


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

    assert c1["study_hours"] == pytest.approx(110 / 60, abs=0.01)
    assert c2["study_hours"] == pytest.approx(105 / 60, abs=0.01)


def test_status_filter_uses_canonical_population():
    filtered = AnalyticsService.filter_data(
        fixture_data(),
        course=ALL_COURSES,
        status="Dropped",
    )

    assert set(filtered.raw["completion"]["student_id"]) == {"S4"}
    assert set(filtered.raw["quiz"]["student_id"]) == {"S4"}
    assert set(filtered.raw["sessions"]["student_id"]) == {"S4"}


def test_all_segments_constant_remains_available():
    assert ALL_SEGMENTS == "All Segments"


def test_course_performance_does_not_require_attempt_number():
    data = fixture_data()
    data.raw["quiz"] = data.raw["quiz"].drop(columns=["attempt_number"])

    result = AnalyticsService().course_performance(data)
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


def test_report_export_schema_is_stable():
    data = fixture_data()
    result = AnalyticsService().report_export_data(data)

    assert list(result.columns) == [
        "student_id",
        "course_id",
        "status",
        "completion_pct",
    ]


def test_report_export_keeps_missing_status_column():
    data = fixture_data()
    data.raw["completion"] = data.raw["completion"].drop(columns=["status"])

    result = AnalyticsService().report_export_data(data)

    assert list(result.columns) == [
        "student_id",
        "course_id",
        "status",
        "completion_pct",
    ]
    assert result["status"].isna().all()


def test_behaviour_by_status_requires_attempt_number():
    data = fixture_data()
    data.raw["quiz"] = data.raw["quiz"].drop(columns=["attempt_number"])

    with pytest.raises(ValueError, match="attempt_number"):
        AnalyticsService().behaviour_by_status(data)
