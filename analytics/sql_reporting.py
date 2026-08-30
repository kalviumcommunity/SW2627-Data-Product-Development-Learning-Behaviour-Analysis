"""SQLite reporting layer for LearnLens analytics."""
from __future__ import annotations
import sqlite3
from collections.abc import Sequence
import pandas as pd

REQUIRED = {
    "student_id","course_id","status","completion_pct","quiz_accuracy",
    "total_study_hours","active_days","learning_streak",
    "days_since_last_activity","weekly_sessions","segment",
}

def _check_conn(conn):
    if not isinstance(conn, sqlite3.Connection):
        raise TypeError("connection must be a sqlite3.Connection")

def _check_table(name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("table_name must be a non-empty string")
    if any(not (c.isalnum() or c == "_") for c in name):
        raise ValueError("table_name contains unsupported characters")

def _exists(conn, name):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone() is not None

def register_student_course(conn, frame, table_name="student_course"):
    """Register and validate the learner analytics table."""
    _check_conn(conn); _check_table(table_name)
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame")
    missing = sorted(REQUIRED - set(frame.columns))
    if missing:
        raise ValueError(
            "student_course is missing required columns: " + ", ".join(missing)
        )
    if frame.duplicated(["student_id","course_id"], keep=False).any():
        raise ValueError("student_course must contain one row per student-course pair")
    frame.to_sql(table_name, conn, if_exists="replace", index=False)

def run_report(conn, query: str, parameters: Sequence[object] = ()):
    """Execute a SELECT query and return a DataFrame."""
    _check_conn(conn)
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    return pd.read_sql_query(query, conn, params=tuple(parameters))

def overall_kpis(conn, table_name="student_course"):
    _check_conn(conn); _check_table(table_name)
    if not _exists(conn, table_name):
        raise ValueError(f"Table does not exist: {table_name}")
    return run_report(conn, f"""
        SELECT COUNT(*) AS learner_course_count,
               COUNT(DISTINCT student_id) AS learner_count,
               COUNT(DISTINCT course_id) AS course_count,
               ROUND(AVG(completion_pct),2) AS avg_completion_pct,
               ROUND(AVG(quiz_accuracy),2) AS avg_quiz_accuracy,
               ROUND(AVG(total_study_hours),2) AS avg_study_hours,
               ROUND(100.0*SUM(CASE WHEN LOWER(TRIM(status))='completed' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) AS completion_rate,
               ROUND(100.0*SUM(CASE WHEN LOWER(TRIM(status))='dropped' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) AS dropoff_rate
        FROM {table_name}
    """)

def course_performance(conn, table_name="student_course"):
    _check_conn(conn); _check_table(table_name)
    if not _exists(conn, table_name):
        raise ValueError(f"Table does not exist: {table_name}")
    return run_report(conn, f"""
        SELECT course_id, COUNT(*) AS learner_count,
               SUM(CASE WHEN LOWER(TRIM(status))='completed' THEN 1 ELSE 0 END) AS completed_count,
               SUM(CASE WHEN LOWER(TRIM(status))='dropped' THEN 1 ELSE 0 END) AS dropped_count,
               ROUND(AVG(completion_pct),2) AS avg_completion_pct,
               ROUND(100.0*SUM(CASE WHEN LOWER(TRIM(status))='completed' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) AS completion_rate,
               ROUND(100.0*SUM(CASE WHEN LOWER(TRIM(status))='dropped' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) AS dropoff_rate,
               ROUND(AVG(quiz_accuracy),2) AS avg_quiz_accuracy,
               ROUND(AVG(total_study_hours),2) AS avg_study_hours
        FROM {table_name}
        GROUP BY course_id
        ORDER BY course_id
    """)

def behaviour_by_status(conn, table_name="student_course"):
    _check_conn(conn); _check_table(table_name)
    if not _exists(conn, table_name):
        raise ValueError(f"Table does not exist: {table_name}")
    return run_report(conn, f"""
        SELECT LOWER(TRIM(status)) AS status, COUNT(*) AS learner_count,
               ROUND(AVG(completion_pct),2) AS avg_completion_pct,
               ROUND(AVG(quiz_accuracy),2) AS avg_quiz_accuracy,
               ROUND(AVG(total_study_hours),2) AS avg_study_hours,
               ROUND(AVG(active_days),2) AS avg_active_days,
               ROUND(AVG(learning_streak),2) AS avg_learning_streak,
               ROUND(AVG(days_since_last_activity),2) AS avg_days_since_last_activity,
               ROUND(AVG(weekly_sessions),2) AS avg_weekly_sessions
        FROM {table_name}
        GROUP BY LOWER(TRIM(status))
        ORDER BY status
    """)

def segment_performance(conn, table_name="student_course"):
    _check_conn(conn); _check_table(table_name)
    if not _exists(conn, table_name):
        raise ValueError(f"Table does not exist: {table_name}")
    return run_report(conn, f"""
        SELECT segment, COUNT(*) AS learner_count,
               ROUND(AVG(completion_pct),2) AS avg_completion_pct,
               ROUND(AVG(quiz_accuracy),2) AS avg_quiz_accuracy,
               ROUND(AVG(total_study_hours),2) AS avg_study_hours,
               ROUND(AVG(days_since_last_activity),2) AS avg_days_since_last_activity,
               SUM(CASE WHEN LOWER(TRIM(status))='completed' THEN 1 ELSE 0 END) AS completed_count,
               SUM(CASE WHEN LOWER(TRIM(status))='dropped' THEN 1 ELSE 0 END) AS dropped_count
        FROM {table_name}
        GROUP BY segment
        ORDER BY learner_count DESC, segment
    """)
