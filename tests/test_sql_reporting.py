"""Tests for the production SQLite reporting layer."""

import sqlite3

import pandas as pd
import pytest

from analytics.sql_reporting import (
    REQUIRED_COLUMNS,
    behaviour_by_status,
    course_performance,
    overall_kpis,
    register_student_course,
    run_report,
    segment_performance,
)


def sample() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "student_id": ["S1", "S2", "S3", "S4"],
            "course_id": ["C1", "C1", "C2", "C2"],
            "status": ["completed", "dropped", "completed", "in_progress"],
            "completion_pct": [100, 40, 100, 60],
            "quiz_accuracy": [85, 55, 80, 70],
            "total_study_hours": [8, 2, 7, 4],
            "active_days": [7, 2, 6, 4],
            "learning_streak": [5, 1, 4, 2],
            "days_since_last_activity": [1, 20, 2, 4],
            "weekly_sessions": [3, 0.5, 2.5, 1.2],
            "segment": ["completed", "at_risk", "completed", "consistent_learner"],
        }
    )


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    register_student_course(connection, sample())
    yield connection
    connection.close()


def test_registration_creates_canonical_table(conn):
    columns = {row[1] for row in conn.execute("PRAGMA table_info(student_course)")}
    assert set(REQUIRED_COLUMNS) <= columns


def test_overall_kpis(conn):
    result = overall_kpis(conn).iloc[0]
    assert result["learner_course_count"] == 4
    assert result["learner_count"] == 4
    assert result["course_count"] == 2
    assert result["avg_completion_pct"] == pytest.approx(75)
    assert result["completion_rate"] == pytest.approx(50)
    assert result["dropoff_rate"] == pytest.approx(25)


def test_course_performance(conn):
    result = course_performance(conn).set_index("course_id")
    assert result.loc["C1", "learner_count"] == 2
    assert result.loc["C1", "completed_count"] == 1
    assert result.loc["C1", "dropped_count"] == 1
    assert result.loc["C1", "completion_rate"] == pytest.approx(50)
    assert result.loc["C2", "completion_rate"] == pytest.approx(50)


def test_status_normalization(conn):
    result = behaviour_by_status(conn)
    assert set(result["status"]) == {"completed", "dropped", "in_progress"}


def test_segment_performance(conn):
    result = segment_performance(conn)
    assert set(result["segment"]) == {"completed", "at_risk", "consistent_learner"}


def test_missing_table_fails():
    connection = sqlite3.connect(":memory:")
    with pytest.raises(ValueError, match="Table does not exist"):
        overall_kpis(connection)
    connection.close()


def test_unsupported_table_name_is_rejected(conn):
    with pytest.raises(ValueError, match="Unsupported reporting table"):
        overall_kpis(conn, "student_course;DROP TABLE student_course")


def test_unknown_report_is_rejected(conn):
    with pytest.raises(ValueError, match="Unknown report"):
        run_report(conn, "arbitrary_sql")


def test_existing_table_is_not_replaced_by_default(conn):
    original_count = conn.execute("SELECT COUNT(*) FROM student_course").fetchone()[0]

    with pytest.raises(ValueError, match="already exists"):
        register_student_course(conn, sample())

    count = conn.execute("SELECT COUNT(*) FROM student_course").fetchone()[0]
    assert count == original_count


def test_replace_requires_explicit_opt_in(conn):
    replacement = sample().iloc[:2].copy()
    register_student_course(conn, replacement, replace=True)

    count = conn.execute("SELECT COUNT(*) FROM student_course").fetchone()[0]
    assert count == 2


def test_quality_contract_rejects_duplicate_student_course():
    connection = sqlite3.connect(":memory:")
    broken = pd.concat([sample(), sample().iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="duplicate student-course"):
        register_student_course(connection, broken)

    connection.close()


def test_quality_contract_requires_expected_columns():
    connection = sqlite3.connect(":memory:")
    broken = sample().drop(columns=["quiz_accuracy"])

    with pytest.raises(ValueError, match="quiz_accuracy"):
        register_student_course(connection, broken)

    connection.close()


def test_missing_status_is_reported_as_unknown():
    connection = sqlite3.connect(":memory:")
    data = sample().copy()
    data.loc[0, "status"] = ""
    register_student_course(connection, data)

    result = behaviour_by_status(connection)
    assert "unknown" in set(result["status"])
    connection.close()


def test_only_select_reports_are_exposed(conn):
    result = run_report(conn, "overall_kpis")
    assert len(result) == 1
