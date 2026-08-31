"""Tests for the stable analytics data contract."""
from __future__ import annotations

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
    return pd.DataFrame(
        {
            "student_id": ["S2", "S1"],
            "course_id": ["C1", "C1"],
            "status": [" In Progress ", "COMPLETED"],
            "completion_pct": [50, 100],
            "segment": ["consistent_learner", "completed"],
            "priority": ["low", "low"],
            "action": ["maintain_consistency", "completion_follow_up"],
            "root_cause": ["no_clear_driver", "completed"],
        }
    )


def course_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "course_id": ["C2", "C1"],
            "learner_count": [10, 20],
            "completed_count": [6, 12],
            "dropped_count": [1, 2],
            "completion_rate": [60, 60],
            "dropoff_rate": [10, 10],
            "avg_completion_pct": [65.5, 75.0],
            "avg_study_hours": [4.25, 5.50],
            "avg_quiz_accuracy": [72.0, 81.0],
            "avg_inactivity_days": [6.5, 4.0],
            "high_priority_count": [2, 3],
        }
    )


def test_contract_version_and_metadata():
    metadata = contract_metadata()

    assert ANALYTICS_CONTRACT_VERSION == "1.0"
    assert metadata["version"] == "1.0"
    assert "student_id" in metadata["learner_columns"]
    assert "course_id" in metadata["course_columns"]


def test_learner_export_has_stable_schema_and_order():
    result = learner_export(learner_data())

    assert list(result.columns) == [
        "student_id",
        "course_id",
        "status",
        "completion_pct",
        "segment",
        "priority",
        "action",
        "root_cause",
    ]
    assert result["student_id"].tolist() == ["S1", "S2"]
    assert result["status"].tolist() == [
        "completed",
        "in_progress",
    ]


def test_course_export_has_stable_schema_and_order():
    result = course_export(course_data())

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
    assert result["course_id"].tolist() == ["C1", "C2"]


def test_learner_duplicate_grain_is_rejected():
    broken = pd.concat(
        [learner_data(), learner_data().iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="one row per student-course pair",
    ):
        learner_export(broken)


def test_learner_invalid_completion_is_rejected():
    broken = learner_data()
    broken.loc[0, "completion_pct"] = 101

    with pytest.raises(
        ValueError,
        match="completion_pct must be within",
    ):
        learner_export(broken)


def test_course_invalid_percentage_is_rejected():
    broken = course_data()
    broken.loc[0, "dropoff_rate"] = 101

    with pytest.raises(
        ValueError,
        match="dropoff_rate must be within",
    ):
        course_export(broken)


def test_missing_required_column_is_rejected():
    with pytest.raises(ValueError, match="segment"):
        learner_export(
            learner_data().drop(columns=["segment"])
        )


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
        "student_id",
        "course_id",
        "status",
        "completion_pct",
        "segment",
        "priority",
        "action",
        "root_cause",
    ]
    assert saved["student_id"].tolist() == ["S1", "S2"]


def test_course_csv_export(tmp_path):
    output = export_csv(
        course_data(),
        tmp_path / "exports" / "courses.csv",
        level="course",
    )

    assert output.exists()

    saved = pd.read_csv(output)
    assert saved["course_id"].tolist() == ["C1", "C2"]


def test_metadata_json_export(tmp_path):
    output = export_contract_metadata(
        tmp_path / "exports" / "analytics_contract.json"
    )

    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["version"] == ANALYTICS_CONTRACT_VERSION
    assert payload["learner_columns"] == [
        "student_id",
        "course_id",
        "status",
        "completion_pct",
        "segment",
        "priority",
        "action",
        "root_cause",
    ]
