"""Tests for segment-level completion and drop-off analytics."""

import pandas as pd
import pytest

from analytics.segment_analysis import analyze_segments


def feature_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "student_id": ["S001", "S002", "S003", "S004", "S005"],
            "course_id": ["C001"] * 5,
            "total_study_hours": [8.0, 1.0, 6.0, 2.0, 4.0],
            "avg_session_length": [60, 30, 60, 20, 45],
            "quiz_accuracy": [85, 80, 45, 70, 65],
            "quiz_frequency": [5, 1, 4, 1, 3],
            "active_days": [7, 1, 6, 1, 4],
            "learning_streak": [5, 1, 4, 1, 2],
            "days_since_last_activity": [1, 20, 2, 3, 2],
            "weekly_sessions": [3.0, 0.5, 2.0, 0.5, 1.5],
            "completion_pct": [100, 35, 60, 20, 50],
            "status": [
                "completed", "dropped", "in_progress",
                "in_progress", "in_progress",
            ],
        }
    )


def test_segment_analysis_returns_expected_schema():
    result = analyze_segments(feature_data())

    assert list(result.columns) == [
        "segment",
        "learner_count",
        "completion_rate",
        "dropoff_rate",
        "avg_completion_pct",
        "avg_study_hours",
        "avg_quiz_accuracy",
        "avg_days_since_last_activity",
    ]


def test_segment_analysis_calculates_metrics():
    result = analyze_segments(feature_data())
    by_segment = result.set_index("segment")

    assert by_segment.loc["completed", "learner_count"] == 1
    assert by_segment.loc["completed", "completion_rate"] == pytest.approx(100.0)
    assert by_segment.loc["completed", "dropoff_rate"] == pytest.approx(0.0)

    assert by_segment.loc["at_risk", "learner_count"] == 1
    assert by_segment.loc["at_risk", "completion_rate"] == pytest.approx(0.0)
    assert by_segment.loc["at_risk", "dropoff_rate"] == pytest.approx(100.0)

    assert by_segment.loc["struggling_learner", "avg_quiz_accuracy"] == pytest.approx(45.0)
    assert by_segment.loc["low_engagement", "avg_study_hours"] == pytest.approx(2.0)
    assert by_segment.loc["consistent_learner", "avg_completion_pct"] == pytest.approx(50.0)


def test_segments_are_sorted_by_dropoff_rate():
    result = analyze_segments(feature_data())
    rates = result["dropoff_rate"].tolist()
    assert rates == sorted(rates, reverse=True)


def test_empty_input_returns_stable_schema():
    empty = feature_data().iloc[0:0].copy()
    result = analyze_segments(empty)

    assert list(result.columns) == [
        "segment",
        "learner_count",
        "completion_rate",
        "dropoff_rate",
        "avg_completion_pct",
        "avg_study_hours",
        "avg_quiz_accuracy",
        "avg_days_since_last_activity",
    ]
    assert result.empty


def test_missing_required_column_fails():
    broken = feature_data().drop(columns=["status"])
    with pytest.raises(ValueError, match="status"):
        analyze_segments(broken)


def test_invalid_numeric_value_fails():
    broken = feature_data()
    broken["quiz_accuracy"] = broken["quiz_accuracy"].astype("object")
    broken.loc[0, "quiz_accuracy"] = "invalid"

    with pytest.raises(ValueError, match="invalid numeric"):
        analyze_segments(broken)


def test_duplicate_student_course_pairs_fail():
    broken = pd.concat(
        [feature_data(), feature_data().iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="duplicate keys"):
        analyze_segments(broken)


def test_completion_and_dropoff_use_source_definitions():
    data = feature_data()
    data.loc[data["student_id"] == "S003", "completion_pct"] = 80

    result = analyze_segments(data)
    by_segment = result.set_index("segment")

    assert by_segment.loc["struggling_learner", "completion_rate"] == pytest.approx(0.0)
    assert by_segment.loc["struggling_learner", "dropoff_rate"] == pytest.approx(0.0)
