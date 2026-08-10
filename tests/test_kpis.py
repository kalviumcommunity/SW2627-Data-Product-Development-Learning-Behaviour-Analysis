"""Unit tests for LearnLens AI core KPI calculations."""

import pandas as pd
import pytest

from analytics.kpis import (
    active_student_count,
    average_quiz_score,
    completion_rate,
    dropoff_rate,
    kpi_summary,
)


@pytest.fixture
def completion_data():
    return pd.DataFrame({
        "student_id": ["S001", "S002", "S003", "S004"],
        "course_id": ["C001"] * 4,
        "status": ["completed", "completed", "dropped", "in_progress"],
        "completion_pct": [100.0, 100.0, 35.0, 60.0],
    })


@pytest.fixture
def quiz_data():
    return pd.DataFrame({
        "student_id": ["S001", "S002", "S003", "S004"],
        "score_pct": [80.0, 90.0, 40.0, 70.0],
    })


@pytest.fixture
def session_data():
    return pd.DataFrame({
        "session_id": ["SE001", "SE002", "SE003", "SE004"],
        "student_id": ["S001", "S001", "S002", "S003"],
        "duration_minutes": [30, 45, 60, 20],
    })


def test_completion_rate(completion_data):
    assert completion_rate(completion_data) == pytest.approx(50.0)


def test_dropoff_rate(completion_data):
    assert dropoff_rate(completion_data) == pytest.approx(25.0)


def test_average_quiz_score(quiz_data):
    assert average_quiz_score(quiz_data) == pytest.approx(70.0)


def test_active_student_count(session_data):
    assert active_student_count(session_data) == 3


def test_empty_data():
    assert completion_rate(pd.DataFrame(columns=["status"])) == 0.0
    assert dropoff_rate(pd.DataFrame(columns=["status"])) == 0.0
    assert average_quiz_score(pd.DataFrame(columns=["score_pct"])) == 0.0
    assert active_student_count(pd.DataFrame(columns=["student_id"])) == 0


def test_all_null_quiz_scores():
    assert average_quiz_score(pd.DataFrame({"score_pct": [None, None]})) == 0.0


def test_missing_columns():
    with pytest.raises(ValueError, match="status"):
        completion_rate(pd.DataFrame({"student_id": ["S001"]}))
    with pytest.raises(ValueError, match="status"):
        dropoff_rate(pd.DataFrame({"student_id": ["S001"]}))
    with pytest.raises(ValueError, match="score_pct"):
        average_quiz_score(pd.DataFrame({"student_id": ["S001"]}))
    with pytest.raises(ValueError, match="student_id"):
        active_student_count(pd.DataFrame({"duration_minutes": [30]}))


def test_kpi_summary(completion_data, quiz_data, session_data):
    result = kpi_summary(completion_data, quiz_data, session_data)
    assert result["completion_rate"] == pytest.approx(50.0)
    assert result["dropoff_rate"] == pytest.approx(25.0)
    assert result["average_quiz_score"] == pytest.approx(70.0)
    assert result["active_students"] == 3