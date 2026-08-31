import pandas as pd
import pytest

from app.services.analytics_service import (
    ALL_COURSES,
    ALL_SEGMENTS,
    ALL_STATUSES,
    AnalyticsService,
    DashboardData,
)


def dashboard():
    return DashboardData(
        raw={
            "completion": pd.DataFrame(
                {
                    "student_id": ["S1", "S2"],
                    "course_id": ["C1", "C1"],
                    "status": ["completed", "in_progress"],
                    "completion_pct": [100, 50],
                }
            ),
            "quiz": pd.DataFrame(
                {
                    "student_id": ["S1", "S2"],
                    "course_id": ["C1", "C1"],
                    "score_pct": [90, 60],
                    "attempt_number": [1, 1],
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


def test_report_export_schema_is_stable():
    result = AnalyticsService().report_export_data(
        dashboard(),
        course=ALL_COURSES,
        status=ALL_STATUSES,
        segment=ALL_SEGMENTS,
    )

    assert list(result.columns) == [
        "student_id",
        "course_id",
        "status",
        "completion_pct",
    ]
