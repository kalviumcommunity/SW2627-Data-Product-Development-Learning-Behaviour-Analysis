"""Tests for canonical pipeline data-quality checks."""

import pandas as pd
import pytest

from pipeline.quality import (
    generate_quality_report,
    validate_student_course_table,
)


def test_quality_report_schema_and_valid_data():
    data = {
        "quiz": pd.DataFrame(
            {
                "student_id": ["S1"],
                "course_id": ["C1"],
                "attempt_number": [1],
                "score_pct": [80],
            }
        )
    }

    result = generate_quality_report(data)

    assert list(result.columns) == [
        "dataset",
        "row_count",
        "missing_values",
        "duplicate_rows",
        "invalid_id_rows",
        "valid",
    ]
    assert bool(result.loc[0, "valid"]) is True


def test_quality_report_counts_quality_issues():
    data = {
        "sessions": pd.DataFrame(
            {
                "student_id": ["S1", "S1", None],
                "course_id": ["C1", "C1", "C2"],
            }
        )
    }

    row = generate_quality_report(data).iloc[0]

    assert row["row_count"] == 3
    assert row["missing_values"] == 1
    assert row["duplicate_rows"] == 2
    assert row["invalid_id_rows"] == 1
    assert bool(row["valid"]) is False


def test_quality_report_rejects_non_dataframe():
    with pytest.raises(
        TypeError,
        match="pandas DataFrame",
    ):
        generate_quality_report({"sessions": []})


def test_empty_dataset_is_invalid():
    result = generate_quality_report(
        {
            "sessions": pd.DataFrame(
                columns=["student_id", "course_id"]
            )
        }
    )
    assert bool(result.loc[0, "valid"]) is False


def test_student_course_valid():
    df = pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "completion_pct": [80],
            "quiz_accuracy": [75],
        }
    )

    pd.testing.assert_frame_equal(
        validate_student_course_table(df),
        df,
    )


def test_student_course_requires_keys():
    with pytest.raises(
        ValueError,
        match="course_id",
    ):
        validate_student_course_table(
            pd.DataFrame({"student_id": ["S1"]})
        )


def test_student_course_rejects_duplicate_keys():
    df = pd.DataFrame(
        {
            "student_id": ["S1", "S1"],
            "course_id": ["C1", "C1"],
        }
    )

    with pytest.raises(
        ValueError,
        match="duplicate student-course keys",
    ):
        validate_student_course_table(df)


def test_student_course_rejects_blank_ids():
    df = pd.DataFrame(
        {
            "student_id": ["S1", " "],
            "course_id": ["C1", "C2"],
        }
    )

    with pytest.raises(
        ValueError,
        match="missing or blank identifiers",
    ):
        validate_student_course_table(df)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("completion_pct", -1),
        ("completion_pct", 101),
        ("quiz_accuracy", -1),
        ("quiz_accuracy", 101),
        ("quiz_accuracy", float("inf")),
    ],
)
def test_student_course_rejects_invalid_metric_range(
    column,
    value,
):
    df = pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            column: [value],
        }
    )

    with pytest.raises(
        ValueError,
        match="invalid values",
    ):
        validate_student_course_table(df)
