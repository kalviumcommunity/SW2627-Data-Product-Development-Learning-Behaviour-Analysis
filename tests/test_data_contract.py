"""Regression tests for the stable analytics data contract."""

import json

import pandas as pd
import pytest

from analytics.data_contract import (
    ANALYTICS_CONTRACT_VERSION,
    contract_metadata,
    course_export,
    export_contract_metadata,
    export_csv,
    learner_export,
)


def learner_data() -> pd.DataFrame:
    return pd.DataFrame({
        "student_id": ["S2", "S1"],
        "course_id": ["C1", "C1"],
        "status": [" In Progress ", "COMPLETED"],
        "completion_pct": [50.0, 100.0],
        "segment": ["consistent_learner", "completed"],
        "priority": ["low", "low"],
        "action": ["maintain_consistency", "completion_follow_up"],
        "root_cause": ["no_clear_driver", "completed"],
    })


def course_data() -> pd.DataFrame:
    return pd.DataFrame({
        "course_id": ["C2", "C1"],
        "learner_count": [10, 20],
        "completed_count": [6, 12],
        "dropped_count": [1, 2],
        "completion_rate": [60.0, 60.0],
        "dropoff_rate": [10.0, 10.0],
        "avg_completion_pct": [65.5, 75.0],
        "avg_study_hours": [4.25, 5.50],
        "avg_quiz_accuracy": [72.0, 81.0],
        "avg_inactivity_days": [6.5, 4.0],
        "high_priority_count": [2, 3],
    })


def test_contract_version_and_metadata():
    metadata = contract_metadata()
    assert ANALYTICS_CONTRACT_VERSION == "1.0"
    assert metadata["version"] == "1.0"
    assert "student_id" in metadata["learner_columns"]
    assert "course_id" in metadata["course_columns"]


def test_learner_export_has_stable_schema_and_order():
    result = learner_export(learner_data())
    assert list(result.columns) == [
        "student_id", "course_id", "status", "completion_pct",
        "segment", "priority", "action", "root_cause",
    ]
    assert result["student_id"].tolist() == ["S1", "S2"]
    assert result["status"].tolist() == ["completed", "in_progress"]


def test_course_export_has_stable_schema_and_order():
    result = course_export(course_data())
    assert list(result.columns) == [
        "course_id", "learner_count", "completed_count", "dropped_count",
        "completion_rate", "dropoff_rate", "avg_completion_pct",
        "avg_study_hours", "avg_quiz_accuracy", "avg_inactivity_days",
        "high_priority_count",
    ]
    assert result["course_id"].tolist() == ["C1", "C2"]


def test_learner_duplicate_grain_is_rejected():
    broken = pd.concat([learner_data(), learner_data().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate student-course keys"):
        learner_export(broken)


def test_learner_invalid_completion_is_rejected():
    broken = learner_data().copy()
    broken["completion_pct"] = broken["completion_pct"].astype(object)
    broken.loc[0, "completion_pct"] = 101
    with pytest.raises(ValueError, match="completion_pct"):
        learner_export(broken)


def test_learner_non_numeric_completion_is_rejected():
    broken = learner_data().copy()
    broken["completion_pct"] = broken["completion_pct"].astype(object)
    broken.loc[0, "completion_pct"] = "not-a-number"

    with pytest.raises(
        ValueError,
        match="completion_pct",
    ):
        learner_export(broken)


@pytest.mark.parametrize(
    "column,value",
    [
        ("segment", "made_up_segment"),
        ("priority", "urgent"),
        ("root_cause", "unknown_cause"),
    ],
)
def test_invalid_categorical_value_is_rejected(column, value):
    broken = learner_data()
    broken.loc[0, column] = value
    with pytest.raises(ValueError, match=column):
        learner_export(broken)


def test_empty_action_is_rejected():
    broken = learner_data()
    broken.loc[0, "action"] = ""
    with pytest.raises(ValueError, match="action"):
        learner_export(broken)


@pytest.mark.parametrize(
    "column,value",
    [
        ("completion_rate", 101),
        ("dropoff_rate", -1),
        ("avg_completion_pct", 101),
        ("avg_quiz_accuracy", -1),
        ("learner_count", -1),
        ("avg_study_hours", -1),
        ("avg_inactivity_days", -1),
    ],
)
def test_invalid_course_metric_is_rejected(column, value):
    broken = course_data().copy()
    broken[column] = broken[column].astype(object)
    broken.loc[0, column] = value
    with pytest.raises(ValueError):
        course_export(broken)


def test_course_non_numeric_value_is_rejected():
    broken = course_data().copy()
    broken["avg_study_hours"] = broken["avg_study_hours"].astype(object)
    broken.loc[0, "avg_study_hours"] = "invalid"
    with pytest.raises(
        ValueError,
        match="avg_study_hours contains non-numeric values",
    ):
        course_export(broken)


def test_missing_required_column_is_rejected():
    with pytest.raises(ValueError, match="segment"):
        learner_export(learner_data().drop(columns=["segment"]))


def test_invalid_level_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="level"):
        export_csv(
            learner_data(),
            tmp_path / "analytics.csv",
            level="unknown",
        )


def test_learner_csv_export(tmp_path):
    output = export_csv(
        learner_data(),
        tmp_path / "exports" / "learners.csv",
    )
    assert output.exists()
    saved = pd.read_csv(output)
    assert list(saved.columns) == [
        "student_id", "course_id", "status", "completion_pct",
        "segment", "priority", "action", "root_cause",
    ]


def test_contract_metadata_export(tmp_path):
    output = export_contract_metadata(
        tmp_path / "metadata" / "contract.json"
    )
    assert output.exists()
    metadata = json.loads(output.read_text(encoding="utf-8"))
    assert metadata["version"] == ANALYTICS_CONTRACT_VERSION
