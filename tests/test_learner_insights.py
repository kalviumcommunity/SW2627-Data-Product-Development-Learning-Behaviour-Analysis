"""Tests for learner insight integration."""
import pandas as pd
import pytest

from analytics.learner_insights import build_learner_insights, insight_summary


def data():
    return pd.DataFrame({
        "student_id": ["S001", "S002", "S003", "S004", "S005"],
        "course_id": ["C001"] * 5,
        "status": ["completed", "dropped", "in_progress", "in_progress", "in_progress"],
        "completion_pct": [100, 35, 60, 20, 50],
        "total_study_hours": [8, 1, 6, 2, 4],
        "avg_session_length": [60, 30, 60, 20, 45],
        "quiz_accuracy": [85, 80, 45, 70, 65],
        "quiz_frequency": [5, 1, 4, 1, 3],
        "active_days": [7, 1, 6, 1, 4],
        "learning_streak": [5, 1, 4, 1, 2],
        "days_since_last_activity": [1, 20, 2, 3, 2],
        "weekly_sessions": [3, 0.5, 2, 0.5, 1.5],
    })


def test_output_schema():
    result = build_learner_insights(data())
    assert list(result.columns) == [
        "student_id", "course_id", "status", "completion_pct",
        "total_study_hours", "avg_session_length", "quiz_accuracy",
        "quiz_frequency", "active_days", "learning_streak",
        "days_since_last_activity", "weekly_sessions",
        "segment", "action", "priority", "message",
    ]


def test_composes_canonical_outputs():
    result = build_learner_insights(data()).set_index("student_id")
    assert result.loc["S001", "segment"] == "completed"
    assert result.loc["S001", "action"] == "completion_follow_up"
    assert result.loc["S002", "segment"] == "at_risk"
    assert result.loc["S002", "action"] == "re_engagement"
    assert result.loc["S003", "segment"] == "struggling_learner"
    assert result.loc["S003", "action"] == "targeted_practice"


def test_preserves_source_metrics():
    row = build_learner_insights(data())
    row = row[row["student_id"] == "S003"].iloc[0]
    assert row["completion_pct"] == 60
    assert row["total_study_hours"] == pytest.approx(6)
    assert row["quiz_accuracy"] == pytest.approx(45)


def test_duplicate_grain_fails():
    broken = pd.concat([data(), data().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="one row per student-course pair"):
        build_learner_insights(broken)


def test_invalid_numeric_fails():
    broken = data()
    broken["quiz_accuracy"] = broken["quiz_accuracy"].astype("object")
    broken.loc[0, "quiz_accuracy"] = "bad"
    with pytest.raises(ValueError, match="invalid numeric"):
        build_learner_insights(broken)


def test_invalid_range_fails():
    broken = data()
    broken.loc[0, "completion_pct"] = 101
    with pytest.raises(ValueError, match="completion_pct"):
        build_learner_insights(broken)


def test_missing_column_fails():
    broken = data().drop(columns=["learning_streak"])
    with pytest.raises(ValueError, match="learning_streak"):
        build_learner_insights(broken)


def test_empty_schema_is_stable():
    result = build_learner_insights(data().iloc[0:0].copy())
    assert result.empty
    assert list(result.columns) == [
        "student_id", "course_id", "status", "completion_pct",
        "total_study_hours", "avg_session_length", "quiz_accuracy",
        "quiz_frequency", "active_days", "learning_streak",
        "days_since_last_activity", "weekly_sessions",
        "segment", "action", "priority", "message",
    ]


def test_summary_totals_and_priority_order():
    result = insight_summary(data())
    assert result["learner_count"].sum() == 5
    assert result["percentage"].sum() == pytest.approx(100.0)
    assert result["priority"].tolist() == sorted(
        result["priority"].tolist(),
        key={"high": 0, "medium": 1, "low": 2}.get,
    )
