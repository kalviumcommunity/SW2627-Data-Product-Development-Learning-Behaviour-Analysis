"""Regression tests for synthetic source-data quality."""

from pipeline.synthetic_data import (
    SyntheticDataConfig,
    generate_synthetic_datasets,
)


def test_default_scale_has_no_duplicate_source_rows():
    data = generate_synthetic_datasets(
        SyntheticDataConfig(
            seed=42,
            students=100,
            courses=5,
            days=90,
        )
    )

    for frame in data.values():
        assert not frame.duplicated().any()


def test_sessions_have_unique_student_course_dates():
    data = generate_synthetic_datasets(
        SyntheticDataConfig(
            seed=42,
            students=100,
            courses=5,
            days=90,
        )
    )

    sessions = data["sessions"]

    assert not sessions.duplicated(
        subset=[
            "student_id",
            "course_id",
            "session_date",
        ]
    ).any()


def test_one_day_calendar_still_generates_valid_sessions():
    data = generate_synthetic_datasets(
        SyntheticDataConfig(
            seed=7,
            students=10,
            courses=2,
            days=1,
        )
    )

    assert not data["sessions"].empty
    assert not data["sessions"].duplicated().any()
