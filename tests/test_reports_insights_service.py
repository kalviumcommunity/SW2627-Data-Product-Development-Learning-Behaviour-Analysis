import pandas as pd

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
                    "student_id": ["S1", "S2", "S3", "S4"],
                    "course_id": ["C1", "C1", "C2", "C2"],
                    "completion_pct": [100, 50, 100, 25],
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
                    "student_id": ["S1", "S2", "S3", "S4"],
                    "course_id": ["C1", "C1", "C2", "C2"],
                    "duration_minutes": [60, 30, 90, 15],
                }
            ),
            "enrollment": pd.DataFrame(
                {
                    "student_id": ["S1", "S2", "S3", "S4"],
                    "course_id": ["C1", "C1", "C2", "C2"],
                }
            ),
        }
    )


def test_report_snapshot_is_data_driven():
    snapshot = AnalyticsService().report_snapshot(
        dashboard_fixture()
    )

    assert snapshot["records"] == 4
    assert snapshot["courses"] == 2
    assert snapshot["active_students"] == 4
    assert snapshot["completion_rate"] == 50.0


def test_status_distribution_normalizes_status():
    result = AnalyticsService().status_distribution(
        dashboard_fixture()
    )

    assert set(result["status"]) == {
        "completed",
        "in_progress",
        "dropped",
    }

    completed = result.loc[
        result["status"] == "completed"
    ].iloc[0]

    assert completed["learners"] == 2


def test_report_export_has_stable_schema():
    result = AnalyticsService().report_export_data(
        dashboard_fixture()
    )

    assert list(result.columns) == [
        "student_id",
        "course_id",
        "status",
        "completion_pct",
    ]
    assert len(result) == 4


def test_status_filter_uses_canonical_population():
    filtered = AnalyticsService.filter_data(
        dashboard_fixture(),
        status="in_progress",
    )

    assert filtered.raw["completion"]["student_id"].tolist() == ["S2"]
    assert filtered.raw["quiz"]["student_id"].tolist() == ["S2"]
    assert filtered.raw["sessions"]["student_id"].tolist() == ["S2"]


def test_all_statuses_preserves_population():
    filtered = AnalyticsService.filter_data(
        dashboard_fixture(),
        status=ALL_STATUSES,
    )

    assert len(filtered.raw["completion"]) == 4
