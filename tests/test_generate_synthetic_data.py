"""Tests for the reproducible synthetic-data generator."""

from __future__ import annotations

import json

import pandas as pd
import pandas.testing as pdt
import pytest

from scripts.generate_synthetic_data import (
    DATASET_COLUMNS,
    generate_datasets,
    write_datasets,
)


def test_generation_is_reproducible():
    first = generate_datasets(
        seed=42,
        students=25,
        courses=4,
        days=30,
    )
    second = generate_datasets(
        seed=42,
        students=25,
        courses=4,
        days=30,
    )

    for name in DATASET_COLUMNS:
        pdt.assert_frame_equal(
            first[name],
            second[name],
        )


def test_seed_changes_generated_data():
    first = generate_datasets(
        seed=1,
        students=25,
        courses=4,
        days=30,
    )
    second = generate_datasets(
        seed=2,
        students=25,
        courses=4,
        days=30,
    )

    assert not first["completion"].equals(
        second["completion"]
    )


def test_generated_schemas_match_raw_contract():
    data = generate_datasets(
        seed=42,
        students=20,
        courses=3,
        days=30,
    )

    for name, columns in DATASET_COLUMNS.items():
        assert list(data[name].columns) == columns


def test_generated_values_respect_domain_ranges():
    data = generate_datasets(
        seed=42,
        students=20,
        courses=3,
        days=30,
    )

    assert data["completion"]["completion_pct"].between(
        0,
        100,
    ).all()

    assert data["sessions"]["duration_minutes"].ge(
        0
    ).all()

    assert data["quiz"]["score"].between(
        0,
        100,
    ).all()

    assert data["quiz"]["attempt"].ge(
        1
    ).all()


def test_student_course_relationships_are_consistent():
    data = generate_datasets(
        seed=42,
        students=40,
        courses=4,
        days=60,
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


def test_writer_creates_csvs_and_manifest(tmp_path):
    paths = write_datasets(
        tmp_path / "generated",
        seed=42,
        students=10,
        courses=3,
        days=30,
    )

    assert set(paths) == {
        "completion",
        "enrollment",
        "sessions",
        "quiz",
        "manifest",
    }

    for name, path in paths.items():
        assert path.exists()

    manifest = json.loads(
        paths["manifest"].read_text(
            encoding="utf-8"
        )
    )

    assert manifest["seed"] == 42
    assert set(manifest["datasets"]) == set(
        DATASET_COLUMNS
    )


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


def test_writer_can_replace_with_force(tmp_path):
    output_dir = tmp_path / "generated"

    first = write_datasets(
        output_dir,
        seed=42,
        students=5,
        courses=2,
        days=14,
    )

    second = write_datasets(
        output_dir,
        seed=99,
        students=5,
        courses=2,
        days=14,
        force=True,
    )

    first_manifest = json.loads(
        first["manifest"].read_text(
            encoding="utf-8"
        )
    )
    second_manifest = json.loads(
        second["manifest"].read_text(
            encoding="utf-8"
        )
    )

    assert first_manifest["seed"] == 42
    assert second_manifest["seed"] == 99
