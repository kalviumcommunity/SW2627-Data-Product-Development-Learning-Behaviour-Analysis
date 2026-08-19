import pandas as pd
import pytest

from analytics.segmentation import segment_learners, segment_summary


BASE = {
    "student_id": ["S001", "S002", "S003", "S004", "S005"],
    "course_id": ["C001"] * 5,
    "total_study_hours": [8, 1, 6, 2, 4],
    "avg_session_length": [60, 30, 60, 20, 45],
    "quiz_accuracy": [85, 80, 45, 70, 65],
    "quiz_frequency": [5, 1, 4, 1, 3],
    "active_days": [7, 1, 6, 1, 4],
    "learning_streak": [5, 1, 4, 1, 2],
    "days_since_last_activity": [1, 20, 2, 3, 2],
    "weekly_sessions": [3, 0.5, 2, 0.5, 1.5],
    "completion_pct": [100, 35, 60, 20, 50],
    "status": ["completed", "in_progress", "in_progress", "in_progress", "in_progress"],
}


@pytest.fixture
def feature_data():
    return pd.DataFrame(BASE)


def test_expected_segments(feature_data):
    result = segment_learners(feature_data)

    assert result["segment"].tolist() == [
        "completed",
        "at_risk",
        "struggling_learner",
        "low_engagement",
        "consistent_learner",
    ]


def test_output_schema(feature_data):
    result = segment_learners(feature_data)

    assert list(result.columns) == [
        "student_id",
        "course_id",
        "segment",
    ]


def test_empty_input_returns_stable_schema(feature_data):
    empty = feature_data.iloc[0:0].copy()

    result = segment_learners(empty)

    assert list(result.columns) == [
        "student_id",
        "course_id",
        "segment",
    ]
    assert result.empty


def test_missing_required_column_fails(feature_data):
    broken = feature_data.drop(columns=["quiz_accuracy"])

    with pytest.raises(ValueError, match="quiz_accuracy"):
        segment_learners(broken)


def test_invalid_numeric_values_fail(feature_data):
    broken = feature_data.copy()
    broken.loc[0, "active_days"] = "invalid"

    with pytest.raises(ValueError, match="invalid numeric"):
        segment_learners(broken)


def test_segment_summary(feature_data):
    result = segment_summary(feature_data)

    assert result["student_count"].sum() == 5
    assert result["percentage"].sum() == pytest.approx(100.0)
    assert set(result["segment"]) == {
        "completed",
        "high_engagement",
        "struggling_learner",
        "at_risk",
        "low_engagement",
        "consistent_learner",
    } - {"high_engagement"}
