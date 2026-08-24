"""Tests for course-level learner analytics."""

from __future__ import annotations

import pandas as pd
import pytest

from analytics.course_insights import course_insights


def sample_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "student_id": ["S1", "S2", "S3", "S4", "S5"],
            "course_id": ["C1", "C1", "C2", "C2", "C2"],
            "status": [
                "completed",
                "dropped",
                "in_progress",
                "dropped",
                "completed",
            ],
            "completion_pct": [100, 40, 65, 20, 100],
            "total_study_hours": [8.0, 2.0, 5.0, 1.0, 7.0],
            "avg_session_length": [60, 30, 45, 20, 55],
            "quiz_accuracy": [85, 55, 72, 40, 80],
            "quiz_frequency": [5, 2, 4, 1, 4],
            "active_days": [7, 2, 5, 1, 6],
            "learning_streak": [5, 1, 3, 1, 4],
            "days_since_last_activity": [1, 20, 3, 18, 2],
            "weekly_sessions": [3.0, 0.5, 2.0, 0.5, 2.5],
        }
    )


def test_course_metrics_use_canonical_status_values():
    result = course_insights(sample_data()).set_index("course_id")

    assert result.loc["C1", "learner_count"] == 2
    assert result.loc["C1", "completed_count"] == 1
    assert result.loc["C1", "dropped_count"] == 1
    assert result.loc["C1", "completion_rate"] == pytest.approx(50.0)
    assert result.loc["C1", "dropoff_rate"] == pytest.approx(50.0)

    assert result.loc["C2", "learner_count"] == 3
    assert result.loc["C2", "completed_count"] == 1
    assert result.loc["C2", "dropped_count"] == 1
    assert result.loc["C2", "completion_rate"] == pytest.approx(33.33, abs=0.01)


def test_status_comparison_is_case_and_whitespace_insensitive():
    data = sample_data()
    data.loc[0, "status"] = " COMPLETED "
    data.loc[1, "status"] = "DROPPED"

    result = course_insights(data).set_index("course_id")

    assert result.loc["C1", "completed_count"] == 1
    assert result.loc["C1", "dropped_count"] == 1


def test_output_schema_is_stable():
    result = course_insights(sample_data())

    assert list(result.columns) == [
        "course_id",
        "learner_count",
        "completed_count",
        "dropped_count",
        "completion_rate",
        "dropoff_rate",
        "avg_completion_pct",
        "avg_study_hours",
        "avg_quiz_accuracy",
        "avg_inactivity_days",
        "high_priority_count",
    ]


def test_course_metrics_include_behavioural_averages():
    result = course_insights(sample_data()).set_index("course_id")

    assert result.loc["C1", "avg_study_hours"] == pytest.approx(5.0)
    assert result.loc["C1", "avg_quiz_accuracy"] == pytest.approx(70.0)
    assert result.loc["C1", "avg_inactivity_days"] == pytest.approx(10.5)


def test_high_priority_count_is_derived_from_existing_recommendations():
    result = course_insights(sample_data()).set_index("course_id")

    assert result.loc["C1", "high_priority_count"] == 1
    assert result.loc["C2", "high_priority_count"] == 1


def test_empty_input_returns_stable_schema():
    result = course_insights(sample_data().iloc[0:0].copy())

    assert result.empty
    assert list(result.columns) == [
        "course_id",
        "learner_count",
        "completed_count",
        "dropped_count",
        "completion_rate",
        "dropoff_rate",
        "avg_completion_pct",
        "avg_study_hours",
        "avg_quiz_accuracy",
        "avg_inactivity_days",
        "high_priority_count",
    ]


def test_missing_required_column_fails_fast():
    broken = sample_data().drop(columns=["quiz_accuracy"])

    with pytest.raises(ValueError, match="quiz_accuracy"):
        course_insights(broken)


def test_duplicate_student_course_grain_is_rejected_by_canonical_layer():
    broken = pd.concat(
        [sample_data(), sample_data().iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="one row per student-course pair",
    ):
        course_insights(broken)
