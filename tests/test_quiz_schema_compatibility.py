"""Regression tests for quiz schema compatibility."""

import pandas as pd
import pytest

from pipeline.clean import clean_quiz
from pipeline.transform import transform_quiz


def new_quiz_schema() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "student_id": ["S1", "S1", "S2"],
            "course_id": ["C1", "C1", "C1"],
            "quiz_id": ["Q1", "Q1", "Q1"],
            "score": [80, 90, 70],
            "attempt": [1, 2, 1],
        }
    )


def canonical_quiz_schema() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "student_id": ["S1", "S1", "S2"],
            "course_id": ["C1", "C1", "C1"],
            "attempt_number": [1, 2, 1],
            "score_pct": [80, 90, 70],
        }
    )


def test_clean_quiz_normalizes_current_raw_schema():
    result = clean_quiz(new_quiz_schema())

    assert "attempt_number" in result.columns
    assert "score_pct" in result.columns
    assert result["attempt_number"].tolist() == [1, 2, 1]
    assert result["score_pct"].tolist() == [80, 90, 70]


def test_clean_quiz_preserves_canonical_schema():
    result = clean_quiz(canonical_quiz_schema())

    assert result["attempt_number"].tolist() == [1, 2, 1]
    assert result["score_pct"].tolist() == [80, 90, 70]


@pytest.mark.parametrize(
    "broken",
    [
        pd.DataFrame(
            {
                "student_id": ["S1"],
                "course_id": ["C1"],
                "score": [80],
            }
        ),
        pd.DataFrame(
            {
                "student_id": ["S1"],
                "course_id": ["C1"],
                "attempt": [1],
            }
        ),
    ],
)
def test_clean_quiz_rejects_incomplete_schema(broken):
    with pytest.raises(ValueError, match="quiz dataset missing"):
        clean_quiz(broken)


def test_transform_quiz_works_with_current_raw_schema_after_cleaning():
    cleaned = clean_quiz(new_quiz_schema())

    result = transform_quiz(cleaned)

    assert list(result.columns) == [
        "student_id",
        "course_id",
        "avg_quiz_score",
        "quiz_attempts",
    ]

    by_pair = result.set_index(["student_id", "course_id"])

    assert by_pair.loc[("S1", "C1"), "avg_quiz_score"] == 85
    assert by_pair.loc[("S1", "C1"), "quiz_attempts"] == 2
    assert by_pair.loc[("S2", "C1"), "avg_quiz_score"] == 70
    assert by_pair.loc[("S2", "C1"), "quiz_attempts"] == 1
