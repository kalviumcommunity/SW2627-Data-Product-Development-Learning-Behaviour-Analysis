"""Tests for automatic synthetic data generation and pipeline integration."""

from __future__ import annotations

import os

import pandas as pd
import pytest
import pandas.testing as pdt

from pipeline.synthetic_data import (
    RAW_COLUMNS,
    SyntheticDataConfig,
    generate_synthetic_datasets,
    write_synthetic_snapshot,
)


def test_same_seed_is_reproducible():
    config = SyntheticDataConfig(
        seed=42,
        students=20,
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


def test_different_seeds_change_generated_data():
    first = generate_synthetic_datasets(
        SyntheticDataConfig(
            seed=1,
            students=20,
            courses=4,
            days=30,
        )
    )
    second = generate_synthetic_datasets(
        SyntheticDataConfig(
            seed=2,
            students=20,
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


def test_snapshot_writer_records_manifest(tmp_path):
    config = SyntheticDataConfig(
        seed=7,
        students=8,
        courses=2,
        days=10,
    )
    data = generate_synthetic_datasets(config)

    paths = write_synthetic_snapshot(
        tmp_path,
        data,
        seed=config.seed,
        config=config,
    )

    assert (tmp_path / "completion.csv").exists()
    assert (tmp_path / "enrollment.csv").exists()
    assert (tmp_path / "sessions.csv").exists()
    assert (tmp_path / "quiz.csv").exists()
    assert paths["manifest"].exists()


def test_invalid_generation_config_is_rejected():
    with pytest.raises(ValueError):
        generate_synthetic_datasets(
            SyntheticDataConfig(
                seed=1,
                students=0,
            )
        )
