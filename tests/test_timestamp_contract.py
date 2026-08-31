"""Regression tests for PR #36 timestamp/schema handling."""

import pandas as pd
import pytest

from pipeline.clean import clean_enrollment, clean_quiz, clean_sessions
from pipeline.validate import validate_all


def test_sessions_normalize_session_date_to_start_time():
    raw = pd.DataFrame({
        "student_id": ["S1", "S1"],
        "course_id": ["C1", "C1"],
        "session_date": ["2024-01-05", "2024-01-07"],
        "duration_minutes": [40, 35],
    })
    result = clean_sessions(raw)

    assert result["start_time"].tolist() == [
        pd.Timestamp("2024-01-05"),
        pd.Timestamp("2024-01-07"),
    ]
    assert result["end_time"].tolist() == [
        pd.Timestamp("2024-01-05 00:40"),
        pd.Timestamp("2024-01-07 00:35"),
    ]


def test_sessions_preserve_extra_source_columns():
    raw = pd.DataFrame({
        "student_id": ["S1"],
        "course_id": ["C1"],
        "session_id": ["SESSION-1"],
        "session_date": ["2024-01-05"],
        "duration_minutes": [30],
    })
    result = clean_sessions(raw)
    assert result["session_id"].tolist() == ["SESSION-1"]


def test_sessions_preserve_exact_start_time():
    raw = pd.DataFrame({
        "student_id": ["S1"],
        "course_id": ["C1"],
        "start_time": ["2024-01-05 14:30:00"],
        "duration_minutes": [45],
    })
    result = clean_sessions(raw)
    assert result.loc[0, "start_time"] == pd.Timestamp("2024-01-05 14:30:00")
    assert result.loc[0, "end_time"] == pd.Timestamp("2024-01-05 15:15:00")


def test_sessions_without_time_fail_instead_of_fabricating():
    raw = pd.DataFrame({
        "student_id": ["S1"],
        "course_id": ["C1"],
        "duration_minutes": [30],
    })
    with pytest.raises(ValueError, match="missing start-time field"):
        clean_sessions(raw)


def test_sessions_invalid_timestamp_fails():
    raw = pd.DataFrame({
        "student_id": ["S1"],
        "course_id": ["C1"],
        "session_date": ["not-a-date"],
        "duration_minutes": [30],
    })
    with pytest.raises(ValueError, match="invalid datetime values"):
        clean_sessions(raw)


def test_sessions_negative_duration_fails():
    raw = pd.DataFrame({
        "student_id": ["S1"],
        "course_id": ["C1"],
        "session_date": ["2024-01-05"],
        "duration_minutes": [-5],
    })
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        clean_sessions(raw)


def test_quiz_current_schema_is_normalized():
    raw = pd.DataFrame({
        "student_id": ["S1", "S1"],
        "course_id": ["C1", "C1"],
        "quiz_id": ["Q1", "Q1"],
        "score": [80, 90],
        "attempt": [1, 2],
    })
    result = clean_quiz(raw)
    assert result["score_pct"].tolist() == [80, 90]
    assert result["attempt_number"].tolist() == [1, 2]


def test_quiz_timestamp_is_not_fabricated():
    raw = pd.DataFrame({
        "student_id": ["S1"],
        "course_id": ["C1"],
        "score": [80],
        "attempt": [1],
    })
    result = clean_quiz(raw)
    assert "timestamp" not in result.columns


def test_quiz_invalid_timestamp_fails():
    raw = pd.DataFrame({
        "student_id": ["S1"],
        "course_id": ["C1"],
        "score": [80],
        "attempt": [1],
        "timestamp": ["not-a-date"],
    })
    with pytest.raises(ValueError, match="quiz.timestamp contains invalid"):
        clean_quiz(raw)


def test_quiz_invalid_score_fails():
    raw = pd.DataFrame({
        "student_id": ["S1"],
        "course_id": ["C1"],
        "score": ["invalid"],
        "attempt": [1],
    })
    with pytest.raises(ValueError, match="quiz.score_pct contains non-numeric"):
        clean_quiz(raw)


def test_enrollment_uses_cleaning_function():
    raw = pd.DataFrame({
        "student_id": ["S1"],
        "course_id": ["C1"],
        "enrollment_date": ["2024-01-05"],
        "cohort": ["A"],
    })
    result = clean_enrollment(raw)
    assert pd.api.types.is_datetime64_any_dtype(result["enrollment_date"])
    validate_all({"enrollment": result})


def test_enrollment_invalid_date_fails():
    raw = pd.DataFrame({
        "student_id": ["S1"],
        "course_id": ["C1"],
        "enrollment_date": ["not-a-date"],
        "cohort": ["A"],
    })
    with pytest.raises(ValueError, match="invalid datetime values"):
        clean_enrollment(raw)


def test_enrollment_missing_date_fails():
    raw = pd.DataFrame({
        "student_id": ["S1"],
        "course_id": ["C1"],
        "enrollment_date": [None],
        "cohort": ["A"],
    })
    with pytest.raises(ValueError, match="missing datetime values"):
        clean_enrollment(raw)
