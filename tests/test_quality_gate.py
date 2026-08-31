"""Tests for the production pipeline data-quality gate."""

from pathlib import Path

import pandas as pd
import pytest

from pipeline.quality_gate import (
    validate_pipeline_output,
    write_quality_report,
)


def source_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "student_id": ["S001", "S002"],
            "course_id": ["C001", "C001"],
            "value": [1, 2],
        }
    )


def student_course_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "student_id": ["S001", "S002"],
            "course_id": ["C001", "C001"],
            "completion_pct": [100, 50],
            "quiz_accuracy": [80, 60],
        }
    )


def test_valid_pipeline_output_returns_quality_report():
    report = validate_pipeline_output(
        {"completion": source_data(), "sessions": source_data()},
        student_course_data(),
    )

    assert list(report["dataset"]) == ["completion", "sessions"]
    assert report["valid"].tolist() == [True, True]


def test_invalid_source_blank_id_blocks_pipeline():
    broken = source_data()
    broken.loc[0, "student_id"] = ""

    with pytest.raises(
        ValueError,
        match="data-quality checks failed.*completion",
    ):
        validate_pipeline_output(
            {"completion": broken},
            student_course_data(),
        )


def test_invalid_source_missing_value_blocks_pipeline():
    broken = source_data()
    broken.loc[0, "value"] = None

    with pytest.raises(
        ValueError,
        match="data-quality checks failed.*completion",
    ):
        validate_pipeline_output(
            {"completion": broken},
            student_course_data(),
        )


def test_invalid_source_duplicate_rows_blocks_pipeline():
    broken = pd.concat(
        [source_data(), source_data().iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="data-quality checks failed.*completion",
    ):
        validate_pipeline_output(
            {"completion": broken},
            student_course_data(),
        )


def test_empty_source_blocks_pipeline():
    broken = source_data().iloc[0:0].copy()

    with pytest.raises(
        ValueError,
        match="data-quality checks failed.*completion",
    ):
        validate_pipeline_output(
            {"completion": broken},
            student_course_data(),
        )


def test_non_dataframe_source_is_rejected():
    with pytest.raises(
        TypeError,
        match="pandas DataFrame",
    ):
        validate_pipeline_output(
            {"completion": []},
            student_course_data(),
        )


def test_duplicate_student_course_keys_block_pipeline():
    broken = pd.concat(
        [student_course_data(), student_course_data().iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="duplicate student-course keys",
    ):
        validate_pipeline_output(
            {"completion": source_data()},
            broken,
        )


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("completion_pct", 101),
        ("completion_pct", -1),
        ("quiz_accuracy", 101),
        ("quiz_accuracy", -1),
    ],
)
def test_invalid_student_course_metric_range_blocks_pipeline(
    column,
    value,
):
    broken = student_course_data()
    broken.loc[0, column] = value

    with pytest.raises(
        ValueError,
        match="invalid values; expected finite values",
    ):
        validate_pipeline_output(
            {"completion": source_data()},
            broken,
        )


def test_non_numeric_student_course_metric_blocks_pipeline():
    broken = student_course_data()
    broken["completion_pct"] = broken["completion_pct"].astype(object)
    broken.loc[0, "completion_pct"] = "invalid"

    with pytest.raises(
        ValueError,
        match="invalid values; expected finite values",
    ):
        validate_pipeline_output(
            {"completion": source_data()},
            broken,
        )


def test_missing_student_course_key_column_blocks_pipeline():
    broken = student_course_data().drop(columns=["course_id"])

    with pytest.raises(
        ValueError,
        match="student_course missing columns: course_id",
    ):
        validate_pipeline_output(
            {"completion": source_data()},
            broken,
        )


def test_quality_report_can_be_written(tmp_path: Path):
    report = pd.DataFrame(
        {
            "dataset": ["completion"],
            "row_count": [2],
            "missing_values": [0],
            "duplicate_rows": [0],
            "invalid_id_rows": [0],
            "valid": [True],
        }
    )

    output = write_quality_report(
        report,
        tmp_path / "reports" / "quality.csv",
    )

    assert output.exists()
    saved = pd.read_csv(output)
    pd.testing.assert_frame_equal(saved, report)


def test_write_quality_report_rejects_invalid_report():
    with pytest.raises(
        TypeError,
        match="pandas DataFrame",
    ):
        write_quality_report(
            {"dataset": "completion"},
            Path("quality.csv"),
        )


def test_strict_pipeline_gate_requires_all_four_sources():
    with pytest.raises(
        ValueError,
        match="data-quality checks failed: missing source dataset",
    ):
        validate_pipeline_output(
            {"completion": source_data()},
            student_course_data(),
            require_all_sources=True,
        )
