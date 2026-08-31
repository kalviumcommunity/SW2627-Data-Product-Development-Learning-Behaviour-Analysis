"""Production pipeline contract regression tests."""

from __future__ import annotations

import pandas as pd
import pytest

from pipeline.clean import (
    clean_completion,
    clean_enrollment,
    clean_quiz,
    clean_sessions,
)
from pipeline.join import build_student_course_table
from pipeline.quality_gate import validate_pipeline_output


def _sources() -> dict[str, pd.DataFrame]:
    return {
        "completion": pd.DataFrame(
            {
                "student_id": ["S1", "S2"],
                "course_id": ["C1", "C1"],
                "completion_pct": [100, 60],
                "status": ["completed", "in_progress"],
            }
        ),
        "enrollment": pd.DataFrame(
            {
                "student_id": ["S1", "S2"],
                "course_id": ["C1", "C1"],
                "enrollment_date": ["2024-01-01", "2024-01-02"],
                "cohort": ["A", "A"],
            }
        ),
        "sessions": pd.DataFrame(
            {
                "student_id": ["S1", "S2"],
                "course_id": ["C1", "C1"],
                "session_date": ["2024-01-05", "2024-01-06"],
                "duration_minutes": [40, 20],
            }
        ),
        "quiz": pd.DataFrame(
            {
                "student_id": ["S1", "S2"],
                "course_id": ["C1", "C1"],
                "score": [90, 70],
                "attempt": [1, 1],
            }
        ),
    }


def test_source_cleaning_produces_canonical_contract():
    data = _sources()

    data["completion"] = clean_completion(data["completion"])
    data["enrollment"] = clean_enrollment(data["enrollment"])
    data["sessions"] = clean_sessions(data["sessions"])
    data["quiz"] = clean_quiz(data["quiz"])

    assert "start_time" in data["sessions"]
    assert "end_time" in data["sessions"]
    assert pd.api.types.is_datetime64_any_dtype(
        data["sessions"]["start_time"]
    )
    assert pd.api.types.is_datetime64_any_dtype(
        data["enrollment"]["enrollment_date"]
    )
    assert {"attempt_number", "score_pct"} <= set(
        data["quiz"].columns
    )


def test_session_timestamp_is_never_fabricated():
    raw = _sources()["sessions"].drop(
        columns=["session_date"]
    )

    with pytest.raises(
        ValueError,
        match="missing start-time field",
    ):
        clean_sessions(raw)


def test_invalid_session_timestamp_fails():
    raw = _sources()["sessions"].copy()
    raw.loc[0, "session_date"] = "2024-99-99"

    with pytest.raises(
        ValueError,
        match="invalid datetime",
    ):
        clean_sessions(raw)


def test_invalid_numeric_source_value_fails():
    raw = _sources()["quiz"].copy()
    raw["score"] = raw["score"].astype(object)
    raw.loc[0, "score"] = "invalid"

    with pytest.raises(
        ValueError,
        match="quiz.score_pct contains non-numeric",
    ):
        clean_quiz(raw)


def test_join_enforces_one_row_per_student_course():
    data = _sources()

    data["completion"] = clean_completion(data["completion"])
    data["enrollment"] = clean_enrollment(data["enrollment"])
    data["sessions"] = clean_sessions(data["sessions"])
    data["quiz"] = clean_quiz(data["quiz"])

    data["sessions"] = (
        data["sessions"]
        .groupby(
            ["student_id", "course_id"],
            as_index=False,
        )
        .agg(
            total_duration=("duration_minutes", "sum"),
            session_count=("duration_minutes", "size"),
        )
    )
    data["quiz"] = (
        data["quiz"]
        .groupby(
            ["student_id", "course_id"],
            as_index=False,
        )
        .agg(
            avg_quiz_score=("score_pct", "mean"),
            quiz_attempts=("attempt_number", "size"),
        )
    )

    result = build_student_course_table(data)

    assert len(result) == 2
    assert not result.duplicated(
        ["student_id", "course_id"]
    ).any()


def test_quality_gate_requires_all_four_source_datasets():
    sources = _sources()
    sources.pop("enrollment")

    student_course = pd.DataFrame(
        {
            "student_id": ["S1"],
            "course_id": ["C1"],
            "completion_pct": [100],
            "quiz_accuracy": [90],
        }
    )

    # require_all_sources=True is the production pipeline contract.
    with pytest.raises(
        ValueError,
        match="missing source dataset",
    ):
        validate_pipeline_output(
            sources,
            student_course,
            require_all_sources=True,
        )


def test_quality_gate_rejects_invalid_source_data():
    sources = _sources()
    cleaned = {
        "completion": clean_completion(sources["completion"]),
        "enrollment": clean_enrollment(sources["enrollment"]),
        "sessions": clean_sessions(sources["sessions"]),
        "quiz": clean_quiz(sources["quiz"]),
    }

    assert set(cleaned) == {
        "completion",
        "enrollment",
        "sessions",
        "quiz",
    }

    with pytest.raises(ValueError):
        bad = dict(cleaned)
        bad["sessions"] = bad["sessions"].copy()
        bad["sessions"].loc[0, "duration_minutes"] = -1
        # The production source cleaner rejects the invalid duration.
        clean_sessions(bad["sessions"])
