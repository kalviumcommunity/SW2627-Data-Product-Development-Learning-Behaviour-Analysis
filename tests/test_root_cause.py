"""Tests for explainable learner root-cause analysis."""
from __future__ import annotations

import pandas as pd
import pytest

from analytics.root_cause import analyze_root_causes, root_cause_summary


def sample_data() -> pd.DataFrame:
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


def test_classifies_expected_drivers():
    result = analyze_root_causes(sample_data())
    assert result["root_cause"].tolist() == [
        "completed", "inactivity", "performance",
        "mixed", "no_clear_driver", "no_clear_driver",
    ]


def test_uses_canonical_segmentation():
    result = analyze_root_causes(sample_data())
    assert result["segment"].tolist() == [
        "completed", "at_risk", "struggling_learner",
        "low_engagement", "consistent_learner", "consistent_learner",
    ]


def test_priority_mapping():
    result = analyze_root_causes(sample_data()).set_index("root_cause")
    assert result.loc["completed", "priority"] == "low"
    assert result.loc["inactivity", "priority"] == "high"
    assert result.loc["performance", "priority"] == "high"
    assert result.loc["mixed", "priority"] == "high"
    assert result.loc["no_clear_driver", "priority"] == "low"


def test_evidence_is_present():
    result = analyze_root_causes(sample_data())
    assert result["evidence"].notna().all()
    assert (result["evidence"].str.len() > 0).all()


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
    data.loc[0, "quiz_accuracy"] = 70
    data.loc[0, "active_days"] = 4
    data.loc[0, "weekly_sessions"] = 1.5

    result = analyze_root_causes(data)

    assert result.loc[0, "root_cause"] == "inactivity"


def test_low_performance_requires_less_than_50():
    data = sample_data()
    data.loc[0, "completion_pct"] = 50
    data.loc[0, "quiz_accuracy"] = 50
    data.loc[0, "active_days"] = 4
    data.loc[0, "weekly_sessions"] = 1.5
    data.loc[0, "days_since_last_activity"] = 2

    result = analyze_root_causes(data)

    assert result.loc[0, "root_cause"] == "no_clear_driver"


def test_empty_input_has_stable_schema():
    result = analyze_root_causes(sample_data().iloc[0:0])

    assert result.empty
    assert list(result.columns) == [
        "student_id", "course_id", "segment",
        "root_cause", "priority", "evidence",
    ]


def test_missing_column_fails():
    with pytest.raises(ValueError, match="quiz_accuracy"):
        analyze_root_causes(
            sample_data().drop(columns=["quiz_accuracy"])
        )


def test_invalid_numeric_value_fails():
    broken = sample_data()
    broken["quiz_accuracy"] = broken["quiz_accuracy"].astype("object")
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

    by_cause = result.set_index("root_cause")
    assert by_cause.loc["inactivity", "learner_count"] == 1
    assert by_cause.loc["performance", "learner_count"] == 1
    assert by_cause.loc["mixed", "learner_count"] == 1


def test_summary_priority_order():
    result = root_cause_summary(sample_data())

    assert result["priority"].tolist() == sorted(
        result["priority"].tolist(),
        key={"high": 0, "medium": 1, "low": 2}.get,
    )
