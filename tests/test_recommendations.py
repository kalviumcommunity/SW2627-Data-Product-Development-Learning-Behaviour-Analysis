"""Tests for deterministic learner recommendations."""

import pandas as pd
import pytest

from analytics.recommendations import (
    generate_recommendations,
    recommendation_summary,
)


def feature_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "student_id": ["S001", "S002", "S003", "S004", "S005", "S006"],
            "course_id": ["C001"] * 6,
            "total_study_hours": [8.0, 1.0, 6.0, 2.0, 4.0, 4.0],
            "quiz_accuracy": [85, 80, 45, 70, 65, 65],
            "active_days": [7, 1, 6, 1, 4, 4],
            "learning_streak": [5, 1, 4, 1, 2, 1],
            "days_since_last_activity": [1, 20, 2, 3, 2, 2],
            "weekly_sessions": [3.0, 0.5, 2.0, 0.5, 1.5, 1.0],
            "completion_pct": [100, 35, 60, 20, 50, 40],
        }
    )


def test_generates_expected_actions_and_priorities():
    result = generate_recommendations(feature_data())

    assert result["action"].tolist() == [
        "completion_follow_up",
        "re_engagement",
        "targeted_practice",
        "engagement_nudge",
        "maintain_consistency",
        "engagement_nudge",
    ]

    assert result["priority"].tolist() == [
        "low",
        "high",
        "high",
        "medium",
        "low",
        "medium",
    ]


def test_output_schema_is_stable():
    result = generate_recommendations(feature_data())

    assert list(result.columns) == [
        "student_id",
        "course_id",
        "segment",
        "action",
        "priority",
        "message",
    ]


def test_messages_are_present():
    result = generate_recommendations(feature_data())

    assert result["message"].notna().all()
    assert (result["message"].str.len() > 0).all()


def test_completed_has_priority_over_risk_signals():
    data = feature_data()
    data.loc[0, "days_since_last_activity"] = 30
    data.loc[0, "quiz_accuracy"] = 20

    result = generate_recommendations(data)

    assert result.loc[0, "segment"] == "completed"
    assert result.loc[0, "action"] == "completion_follow_up"


def test_empty_input_returns_stable_schema():
    result = generate_recommendations(feature_data().iloc[0:0].copy())

    assert result.empty
    assert list(result.columns) == [
        "student_id",
        "course_id",
        "segment",
        "action",
        "priority",
        "message",
    ]


def test_missing_feature_fails():
    broken = feature_data().drop(columns=["quiz_accuracy"])

    with pytest.raises(ValueError, match="quiz_accuracy"):
        generate_recommendations(broken)


def test_invalid_numeric_feature_fails():
    broken = feature_data()
    broken["quiz_accuracy"] = broken["quiz_accuracy"].astype("object")
    broken.loc[0, "quiz_accuracy"] = "invalid"

    with pytest.raises(ValueError, match="invalid numeric"):
        generate_recommendations(broken)


def test_invalid_completion_range_fails():
    broken = feature_data()
    broken.loc[0, "completion_pct"] = 101

    with pytest.raises(ValueError, match="completion_pct"):
        generate_recommendations(broken)


def test_duplicate_student_course_pair_fails():
    broken = pd.concat(
        [feature_data(), feature_data().iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="one row per student-course pair",
    ):
        generate_recommendations(broken)


def test_summary_counts_and_percentages():
    result = recommendation_summary(feature_data())

    assert result["learner_count"].sum() == 6
    assert result["percentage"].sum() == pytest.approx(100.0)

    by_action = result.set_index("action")
    assert by_action.loc["re_engagement", "learner_count"] == 1
    assert by_action.loc["targeted_practice", "learner_count"] == 1
    assert by_action.loc["engagement_nudge", "learner_count"] == 2


def test_summary_prioritizes_high_before_medium_and_low():
    result = recommendation_summary(feature_data())

    priorities = result["priority"].tolist()
    assert priorities == sorted(
        priorities,
        key={"high": 0, "medium": 1, "low": 2}.get,
    )
