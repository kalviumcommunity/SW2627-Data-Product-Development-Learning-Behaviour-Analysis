"""Regression tests for root-cause analytics."""
from __future__ import annotations

import pandas as pd
import pytest

from analytics.root_cause import analyze_root_causes, root_cause_summary


def sample_data():
    return pd.DataFrame({
        "student_id": ["S001", "S002", "S003", "S004", "S005", "S006"],
        "course_id": ["C001"] * 6,
        "total_study_hours": [8, 4, 6, 2, 4, 4],
        "quiz_accuracy": [85, 80, 40, 40, 65, 70],
        "active_days": [7, 4, 6, 1, 4, 4],
        "learning_streak": [5, 3, 4, 1, 2, 2],
        "days_since_last_activity": [1, 20, 2, 20, 2, 3],
        "weekly_sessions": [3, 1.5, 2, 0.5, 1.5, 1.2],
        "completion_pct": [100, 35, 60, 30, 50, 60],
    })


def test_root_cause_uses_canonical_segmentation():
    result = analyze_root_causes(sample_data())

    assert result["segment"].tolist() == [
        "completed",
        "at_risk",
        "struggling_learner",
        "at_risk",
        "consistent_learner",
        "consistent_learner",
    ]


def test_priority_mapping_is_unique_per_driver():
    result = analyze_root_causes(sample_data())

    priorities = (
        result[["root_cause", "priority"]]
        .drop_duplicates("root_cause")
        .set_index("root_cause")["priority"]
        .to_dict()
    )

    assert priorities == {
        "completed": "low",
        "inactivity": "high",
        "performance": "high",
        "mixed": "high",
        "no_clear_driver": "low",
    }


def test_output_schema():
    result = analyze_root_causes(sample_data())

    assert list(result.columns) == [
        "student_id",
        "course_id",
        "segment",
        "root_cause",
        "priority",
        "evidence",
    ]


def test_completion_overrides_other_signals():
    data = sample_data()
    data.loc[0, "days_since_last_activity"] = 30
    data.loc[0, "quiz_accuracy"] = 20

    result = analyze_root_causes(data)

    assert result.loc[0, "root_cause"] == "completed"
    assert result.loc[0, "priority"] == "low"


def test_inactivity_threshold_is_inclusive():
    data = sample_data()
    data.loc[0, "completion_pct"] = 50
    data.loc[0, "days_since_last_activity"] = 14
    data.loc[0, "active_days"] = 4
    data.loc[0, "weekly_sessions"] = 1.5
    data.loc[0, "quiz_accuracy"] = 70

    result = analyze_root_causes(data)

    assert result.loc[0, "root_cause"] == "inactivity"


def test_empty_input_has_stable_schema():
    result = analyze_root_causes(sample_data().iloc[0:0])

    assert result.empty
    assert list(result.columns) == [
        "student_id",
        "course_id",
        "segment",
        "root_cause",
        "priority",
        "evidence",
    ]


def test_invalid_numeric_value_fails():
    broken = sample_data()
    broken["quiz_accuracy"] = broken["quiz_accuracy"].astype(object)
    broken.loc[0, "quiz_accuracy"] = "invalid"

    with pytest.raises(ValueError, match="invalid numeric"):
        analyze_root_causes(broken)


def test_invalid_completion_range_fails():
    broken = sample_data()
    broken.loc[0, "completion_pct"] = 101

    with pytest.raises(ValueError, match="completion_pct"):
        analyze_root_causes(broken)


def test_duplicate_student_course_pair_fails():
    broken = pd.concat(
        [sample_data(), sample_data().iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="one row per student-course pair",
    ):
        analyze_root_causes(broken)


def test_summary_counts_and_percentages():
    result = root_cause_summary(sample_data())

    assert result["learner_count"].sum() == 6
    assert result["percentage"].sum() == pytest.approx(100.0)
    assert set(result["root_cause"]) == {
        "completed",
        "inactivity",
        "performance",
        "mixed",
        "no_clear_driver",
    }
