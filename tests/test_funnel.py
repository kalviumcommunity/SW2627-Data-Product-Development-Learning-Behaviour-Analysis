"""Tests for course completion funnel analytics."""

import pandas as pd
import pytest

from analytics.funnel import build_completion_funnel


@pytest.fixture
def feature_data():
    return pd.DataFrame({
        "student_id": ["S001", "S002", "S003", "S004", "S005"],
        "course_id": ["C001"] * 5,
        "completion_pct": [100, 80, 50, 25, 0],
    })


def test_funnel_counts_are_cumulative(feature_data):
    result = build_completion_funnel(feature_data)
    assert result["student_count"].tolist() == [5, 4, 4, 3, 2, 1]


def test_conversion_rate_uses_enrolled_as_denominator(feature_data):
    result = build_completion_funnel(feature_data)
    assert result.loc[1, "conversion_rate"] == pytest.approx(80.0)
    assert result.loc[3, "conversion_rate"] == pytest.approx(60.0)
    assert result.loc[5, "conversion_rate"] == pytest.approx(20.0)


def test_dropoff_rate_uses_previous_stage(feature_data):
    result = build_completion_funnel(feature_data)
    assert result.loc[0, "dropoff_rate"] == pytest.approx(0.0)
    assert result.loc[1, "dropoff_rate"] == pytest.approx(20.0)
    assert result.loc[3, "dropoff_rate"] == pytest.approx(25.0)
    assert result.loc[4, "dropoff_rate"] == pytest.approx(33.33)
    assert result.loc[5, "dropoff_rate"] == pytest.approx(50.0)


def test_duplicate_student_course_records_do_not_double_count():
    data = pd.DataFrame({
        "student_id": ["S001", "S001", "S002"],
        "course_id": ["C001", "C001", "C001"],
        "completion_pct": [50, 50, 100],
    })
    result = build_completion_funnel(data)
    assert result.loc[0, "student_count"] == 2
    assert result.loc[3, "student_count"] == 2
    assert result.loc[5, "student_count"] == 1


def test_invalid_completion_values_are_ignored():
    data = pd.DataFrame({
        "student_id": ["S001", "S002", "S003"],
        "course_id": ["C001"] * 3,
        "completion_pct": [100, "invalid", None],
    })
    result = build_completion_funnel(data)
    assert result.loc[0, "student_count"] == 1
    assert result.loc[5, "student_count"] == 1


def test_empty_dataframe_has_stable_schema():
    data = pd.DataFrame(columns=["student_id", "course_id", "completion_pct"])
    result = build_completion_funnel(data)
    assert list(result.columns) == [
        "stage", "student_count", "conversion_rate", "dropoff_rate"
    ]
    assert result.empty


def test_missing_required_column_fails():
    data = pd.DataFrame({"student_id": ["S001"], "course_id": ["C001"]})
    with pytest.raises(ValueError, match="completion_pct"):
        build_completion_funnel(data)
