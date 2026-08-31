"""Tests for pipeline timestamp and schema normalization."""
from __future__ import annotations

import pandas as pd
import pytest

from pipeline.clean import clean_quiz, clean_sessions
from pipeline.validate import validate_all


def test_sessions_normalize_session_date_to_start_time():
    raw = pd.DataFrame(
        {
            "student_id": ["S1", "S1"],
            "course_id": ["C1", "C1"],
            "session_date": [
                "2024-01-05",
                "2024-01-07",
            ],
            "duration_minutes": [40, 35],
        }
    )

    result = clean_sessions(raw)

    assert pd.api.types.is_datetime64_any_dtype(
        result["start_time"]
    )
    assert result["start_time"].tolist() == [
        pd.Timestamp("2024-01-05"),
        pd.Timestamp("2024-01-07"),
    ]
    assert result["end_time"].tolist() == [
        pd.Timestamp("2024-01-05 00:40"),
        pd.Timestamp("2024-01-07 00:35"),
    ]


def test_sessions_preserve_exact_start_time_when_available():
    raw = pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "start_time": ["2024-01-05 14:30:00"],
            "duration_minutes": [45],
        }
    )

    result = clean_sessions(raw)

    assert result.loc[0, "start_time"] == pd.Timestamp(
        "2024-01-05 14:30:00"
    )
    assert result.loc[0, "end_time"] == pd.Timestamp(
        "2024-01-05 15:15:00"
    )


def test_sessions_reject_negative_duration():
    raw = pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "session_date": ["2024-01-05"],
            "duration_minutes": [-5],
        }
    )

    with pytest.raises(ValueError, match="greater than or equal to 0"):
        clean_sessions(raw)


def test_sessions_missing_time_field_fails():
    raw = pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "duration_minutes": [30],
        }
    )

    with pytest.raises(ValueError, match="start-time"):
        clean_sessions(raw)


def test_quiz_current_raw_schema_is_normalized():
    raw = pd.DataFrame(
        {
            "student_id": ["S1", "S1"],
            "course_id": ["C1", "C1"],
            "quiz_id": ["Q1", "Q1"],
            "score": [80, 90],
            "attempt": [1, 2],
        }
    )

    result = clean_quiz(raw)

    assert result["score_pct"].tolist() == [80, 90]
    assert result["attempt_number"].tolist() == [1, 2]
    assert "timestamp" not in result.columns


def test_quiz_timestamp_is_standardized_when_present():
    raw = pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "quiz_id": ["Q1"],
            "score": [80],
            "attempt": [1],
            "timestamp": ["2024-01-05 13:00:00"],
        }
    )

    result = clean_quiz(raw)

    assert result.loc[0, "timestamp"] == pd.Timestamp(
        "2024-01-05 13:00:00"
    )


def test_cleaned_sessions_satisfy_schema_contract():
    sessions = clean_sessions(
        pd.DataFrame(
            {
                "student_id": ["S1"],
                "course_id": ["C1"],
                "session_date": ["2024-01-05"],
                "duration_minutes": [30],
            }
        )
    )

    validate_all(
        {
            "sessions": sessions,
        }
    )


def test_validation_rejects_unknown_dataset():
    with pytest.raises(ValueError, match="Unknown datasets"):
        validate_all(
            {
                "unexpected": pd.DataFrame(),
            }
        )


def test_validation_rejects_duplicate_rows():
    sessions = clean_sessions(
        pd.DataFrame(
            {
                "student_id": ["S1", "S1"],
                "course_id": ["C1", "C1"],
                "session_date": [
                    "2024-01-05",
                    "2024-01-05",
                ],
                "duration_minutes": [30, 30],
            }
        )
    )

    with pytest.raises(ValueError, match="duplicate rows"):
        validate_all({"sessions": sessions})


def test_validation_requires_canonical_session_time():
    broken = pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "duration_minutes": [30],
        }
    )

    with pytest.raises(ValueError, match="sessions missing columns"):
        validate_all({"sessions": broken})
