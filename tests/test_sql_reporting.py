import sqlite3
import pandas as pd
import pytest

from analytics.sql_reporting import (
    register_student_course, overall_kpis, course_performance,
    behaviour_by_status, segment_performance, run_report
)

def sample():
    return pd.DataFrame({
        "student_id":["S1","S2","S3","S4"],
        "course_id":["C1","C1","C2","C2"],
        "status":["completed","dropped","completed","in_progress"],
        "completion_pct":[100,40,100,60],
        "quiz_accuracy":[85,55,80,70],
        "total_study_hours":[8,2,7,4],
        "active_days":[7,2,6,4],
        "learning_streak":[5,1,4,2],
        "days_since_last_activity":[1,20,2,4],
        "weekly_sessions":[3,.5,2.5,1.2],
        "segment":["completed","at_risk","completed","consistent_learner"],
    })

@pytest.fixture
def conn():
    c=sqlite3.connect(":memory:")
    register_student_course(c, sample())
    yield c
    c.close()

def test_overall_kpis(conn):
    r=overall_kpis(conn).iloc[0]
    assert r["learner_course_count"] == 4
    assert r["learner_count"] == 4
    assert r["course_count"] == 2
    assert r["avg_completion_pct"] == pytest.approx(75)
    assert r["completion_rate"] == pytest.approx(50)
    assert r["dropoff_rate"] == pytest.approx(25)

def test_course_performance(conn):
    r=course_performance(conn).set_index("course_id")
    assert r.loc["C1","learner_count"] == 2
    assert r.loc["C1","completed_count"] == 1
    assert r.loc["C1","dropped_count"] == 1
    assert r.loc["C1","completion_rate"] == pytest.approx(50)
    assert r.loc["C2","completion_rate"] == pytest.approx(50)

def test_status_normalization(conn):
    conn.execute("UPDATE student_course SET status=' COMPLETED ' WHERE student_id='S4'")
    r=behaviour_by_status(conn).set_index("status")
    assert r.loc["completed","learner_count"] == 3

def test_segment_performance(conn):
    r=segment_performance(conn).set_index("segment")
    assert r.loc["completed","learner_count"] == 2
    assert r.loc["at_risk","dropped_count"] == 1

def test_missing_table_fails():
    c=sqlite3.connect(":memory:")
    with pytest.raises(ValueError, match="Table does not exist"):
        overall_kpis(c)
    c.close()

def test_missing_columns_fail():
    c=sqlite3.connect(":memory:")
    with pytest.raises(ValueError, match="quiz_accuracy"):
        register_student_course(c, sample().drop(columns=["quiz_accuracy"]))
    c.close()

def test_duplicate_grain_fails():
    c=sqlite3.connect(":memory:")
    broken=pd.concat([sample(), sample().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="one row per student-course pair"):
        register_student_course(c, broken)
    c.close()

def test_invalid_table_name_fails(conn):
    with pytest.raises(ValueError, match="unsupported"):
        overall_kpis(conn, "student_course;DROP_TABLE")

def test_parameterized_query(conn):
    r=run_report(conn,
        "SELECT COUNT(*) AS n FROM student_course WHERE course_id=?",
        ["C1"])
    assert r.loc[0,"n"] == 2
