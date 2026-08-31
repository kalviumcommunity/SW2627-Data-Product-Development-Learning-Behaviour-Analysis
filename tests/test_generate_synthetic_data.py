"""Tests for the reproducible synthetic-data generator."""

from __future__ import annotations

import json

import pandas.testing as pdt
import pytest

from pipeline.synthetic_data import (
    RAW_COLUMNS,
    SyntheticDataConfig,
    generate_synthetic_datasets,
)
from tests.synthetic_writer_compat import write_datasets


def test_generation_is_reproducible():
    config = SyntheticDataConfig(
        seed=42,
        students=25,
        courses=4,
        days=30,
    )

    first = generate_synthetic_datasets(config)
    second = generate_synthetic_datasets(config)

    for name in RAW_COLUMNS:
        pdt.assert_frame_equal(
            first[name],
            second[name],
        )


def test_seed_changes_generated_data():
    first = generate_synthetic_datasets(
        SyntheticDataConfig(
            seed=1,
            students=25,
            courses=4,
            days=30,
        )
    )
    second = generate_synthetic_datasets(
        SyntheticDataConfig(
            seed=2,
            students=25,
            courses=4,
            days=30,
        )
    )

    assert not first["completion"].equals(
        second["completion"]
    )


def test_no_seed_produces_fresh_runs():
    first = generate_synthetic_datasets(
        SyntheticDataConfig(
            seed=None,
            students=20,
            courses=4,
            days=30,
        )
    )
    second = generate_synthetic_datasets(
        SyntheticDataConfig(
            seed=None,
            students=20,
            courses=4,
            days=30,
        )
    )

    assert not first["completion"].equals(
        second["completion"]
    )


def test_raw_schemas_match_current_pipeline_contract():
    data = generate_synthetic_datasets(
        SyntheticDataConfig(
            seed=42,
            students=10,
            courses=3,
            days=14,
        )
    )

    for name, columns in RAW_COLUMNS.items():
        assert list(data[name].columns) == columns


def test_generated_relationships_are_consistent():
    data = generate_synthetic_datasets(
        SyntheticDataConfig(
            seed=42,
            students=30,
            courses=4,
            days=30,
        )
    )

    completion_keys = set(
        zip(
            data["completion"]["student_id"],
            data["completion"]["course_id"],
        )
    )
    enrollment_keys = set(
        zip(
            data["enrollment"]["student_id"],
            data["enrollment"]["course_id"],
        )
    )
    session_keys = set(
        zip(
            data["sessions"]["student_id"],
            data["sessions"]["course_id"],
        )
    )
    quiz_keys = set(
        zip(
            data["quiz"]["student_id"],
            data["quiz"]["course_id"],
        )
    )

    assert enrollment_keys == completion_keys
    assert session_keys <= completion_keys
    assert quiz_keys <= completion_keys


def test_writer_creates_all_files(tmp_path):
    paths = write_datasets(
        tmp_path / "generated",
        seed=42,
        students=8,
        courses=2,
        days=10,
    )

    assert set(paths) == {
        "completion",
        "enrollment",
        "sessions",
        "quiz",
        "manifest",
    }

    for path in paths.values():
        assert path.exists()


def test_writer_can_replace_with_force(tmp_path):
    output_dir = tmp_path / "generated"

    first = write_datasets(
        output_dir,
        seed=42,
        students=5,
        courses=2,
        days=14,
    )

    # Snapshot the first manifest before force-overwriting it.
    first_manifest = json.loads(
        first["manifest"].read_text(
            encoding="utf-8"
        )
    )

    second = write_datasets(
        output_dir,
        seed=99,
        students=5,
        courses=2,
        days=14,
        force=True,
    )

    second_manifest = json.loads(
        second["manifest"].read_text(
            encoding="utf-8"
        )
    )

    assert first_manifest["seed"] == 42
    assert second_manifest["seed"] == 99


def test_writer_does_not_overwrite_without_force(tmp_path):
    output_dir = tmp_path / "generated"

    write_datasets(
        output_dir,
        seed=42,
        students=5,
        courses=2,
        days=14,
    )

    with pytest.raises(FileExistsError):
        write_datasets(
            output_dir,
            seed=99,
            students=5,
            courses=2,
            days=14,
        )
