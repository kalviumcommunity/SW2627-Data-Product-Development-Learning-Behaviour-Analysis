"""Regression tests for behavioural relationship analysis."""
import pandas as pd
import pytest

from analytics.relationship_analysis import (
    BEHAVIOURAL_COLUMNS,
    correlate_with_completion,
    correlation_matrix,
    strongest_relationships,
)


def data():
    return pd.DataFrame({
        "student_id": ["S1","S2","S3","S4","S5"],
        "course_id": ["C1"] * 5,
        "total_study_hours": [1,2,3,4,5],
        "avg_session_length": [20,30,40,50,60],
        "quiz_accuracy": [40,50,60,70,80],
        "quiz_frequency": [1,2,3,4,5],
        "active_days": [1,2,3,4,5],
        "learning_streak": [1,2,3,4,5],
        "days_since_last_activity": [10,8,6,4,2],
        "weekly_sessions": [1,2,3,4,5],
        "completion_pct": [20,35,50,65,80],
    })


def test_schema_and_feature_count():
    result = correlate_with_completion(data())
    assert list(result.columns) == [
        "feature","target","sample_size","correlation",
        "abs_correlation","strength","direction",
    ]
    assert len(result) == len(BEHAVIOURAL_COLUMNS)


def test_positive_relationship():
    row = correlate_with_completion(data()).set_index("feature").loc["quiz_accuracy"]
    assert row["sample_size"] == 5
    assert row["correlation"] == pytest.approx(1.0)
    assert row["strength"] == "strong"
    assert row["direction"] == "positive"


def test_negative_relationship():
    row = correlate_with_completion(data()).set_index(
        "feature"
    ).loc["days_since_last_activity"]
    assert row["correlation"] < 0
    assert row["direction"] == "negative"


def test_pairwise_missing_values_are_supported():
    broken = data()
    broken.loc[0, "quiz_accuracy"] = None
    row = correlate_with_completion(broken).set_index(
        "feature"
    ).loc["quiz_accuracy"]

    assert row["sample_size"] == 4
    assert row["correlation"] is not None
    assert row["correlation"] == pytest.approx(1.0)


def test_invalid_non_numeric_value_is_rejected():
    broken = data()
    broken["quiz_accuracy"] = broken["quiz_accuracy"].astype(object)
    broken.loc[0, "quiz_accuracy"] = "invalid"

    with pytest.raises(
        ValueError,
        match="quiz_accuracy contains non-numeric values",
    ):
        correlate_with_completion(broken)


def test_completion_range_is_enforced():
    broken = data()
    broken.loc[0, "completion_pct"] = 101

    with pytest.raises(
        ValueError,
        match="completion_pct must be within",
    ):
        correlate_with_completion(broken)


def test_negative_behaviour_value_is_rejected():
    broken = data()
    broken.loc[0, "weekly_sessions"] = -1

    with pytest.raises(
        ValueError,
        match="weekly_sessions must be greater than or equal to 0",
    ):
        correlate_with_completion(broken)


def test_constant_feature_is_undefined():
    broken = data()
    broken["active_days"] = 3

    row = correlate_with_completion(broken).set_index(
        "feature"
    ).loc["active_days"]

    assert pd.isna(row["correlation"])
    assert row["strength"] == "undefined"
    assert row["direction"] == "unknown"


def test_insufficient_data_is_explicit():
    row = correlate_with_completion(data().iloc[:1]).set_index(
        "feature"
    ).loc["quiz_accuracy"]

    assert row["sample_size"] == 1
    assert pd.isna(row["correlation"])
    assert row["strength"] == "insufficient_data"


def test_matrix_shape_and_symmetry():
    result = correlation_matrix(data())
    columns = BEHAVIOURAL_COLUMNS + ["completion_pct"]

    assert list(result.columns) == columns
    assert list(result.index) == columns
    pd.testing.assert_frame_equal(result, result.T)


def test_strongest_relationship_limit():
    result = strongest_relationships(data(), limit=3)
    assert len(result) == 3
    assert result["abs_correlation"].tolist() == sorted(
        result["abs_correlation"].tolist(),
        reverse=True,
    )


def test_invalid_limit():
    with pytest.raises(ValueError, match="positive integer"):
        strongest_relationships(data(), limit=0)


def test_missing_required_column():
    with pytest.raises(ValueError, match="quiz_accuracy"):
        correlate_with_completion(
            data().drop(columns=["quiz_accuracy"])
        )


def test_numeric_strings_are_supported():
    converted = data()
    converted["quiz_accuracy"] = converted["quiz_accuracy"].astype(str)

    row = correlate_with_completion(converted).set_index(
        "feature"
    ).loc["quiz_accuracy"]

    assert row["correlation"] == pytest.approx(1.0)


def test_empty_input_schema():
    result = correlate_with_completion(data().iloc[0:0])

    assert result.empty
    assert list(result.columns) == [
        "feature","target","sample_size","correlation",
        "abs_correlation","strength","direction",
    ]
