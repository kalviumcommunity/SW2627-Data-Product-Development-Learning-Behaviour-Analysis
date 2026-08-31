import pandas as pd
import pytest

from app.services.analytics_service import (
    ALL_STATUSES,
    AnalyticsService,
    DashboardData,
)


def dashboard_fixture() -> DashboardData:
    return DashboardData(
        raw={
            "completion": pd.DataFrame(
                {
                    "student_id": ["S1", "S2"],
                    "course_id": ["C1", "C1"],
                    "completion_pct": [100, 50],
                    "status": ["completed", "in_progress"],
                }
            ),
            "quiz": pd.DataFrame(
                {
                    "student_id": ["S1", "S2"],
                    "course_id": ["C1", "C1"],
                    "score_pct": [90, 60],
                    "attempt_number": [1, 2],
                }
            ),
            "sessions": pd.DataFrame(
                {
                    "student_id": ["S1", "S2"],
                    "course_id": ["C1", "C1"],
                    "duration_minutes": [60, 30],
                }
            ),
        }
    )


def test_report_snapshot_is_data_driven():
    snapshot = AnalyticsService().report_snapshot(dashboard_fixture())

    assert snapshot["records"] == 2
    assert snapshot["courses"] == 1
    assert snapshot["active_students"] == 2


def test_status_distribution_normalizes_status():
    result = AnalyticsService().status_distribution(dashboard_fixture())

    assert set(result["status"]) == {"completed", "in_progress"}


def test_report_export_schema_is_stable():
    data = dashboard_fixture()
    data.raw["completion"] = data.raw["completion"].drop(
        columns=["status"]
    )

    result = AnalyticsService().report_export_data(data)

    assert list(result.columns) == [
        "student_id",
        "course_id",
        "status",
        "completion_pct",
    ]
    assert result["status"].isna().all()


def test_report_export_normalizes_values():
    result = AnalyticsService().report_export_data(dashboard_fixture())

    assert result["status"].tolist() == [
        "completed",
        "in_progress",
    ]
    assert result["completion_pct"].tolist() == [
        100.0,
        50.0,
    ]


def test_behaviour_by_status_requires_attempt_number():
    data = dashboard_fixture()
    data.raw["quiz"] = data.raw["quiz"].drop(
        columns=["attempt_number"]
    )

    with pytest.raises(ValueError, match="attempt_number"):
        AnalyticsService().behaviour_by_status(data)
