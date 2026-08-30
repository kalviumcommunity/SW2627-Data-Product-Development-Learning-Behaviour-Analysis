"""SQLite reporting layer for LearnLens analytics."""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from pipeline.quality import validate_student_course_table

REQUIRED_COLUMNS = (
    "student_id", "course_id", "status", "completion_pct",
    "quiz_accuracy", "total_study_hours", "active_days",
    "learning_streak", "days_since_last_activity",
    "weekly_sessions", "segment",
)
DEFAULT_TABLE = "student_course"
ALLOWED_TABLES = frozenset({DEFAULT_TABLE})
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SQL_DIR = Path(__file__).resolve().parent / "sql_queries"


def _check_connection(conn: sqlite3.Connection) -> None:
    if not isinstance(conn, sqlite3.Connection):
        raise TypeError("connection must be a sqlite3.Connection")


def _check_table_name(table_name: str) -> None:
    if not isinstance(table_name, str) or not table_name.strip():
        raise ValueError("table_name must be a non-empty string")
    if table_name not in ALLOWED_TABLES:
        raise ValueError(
            f"Unsupported reporting table: {table_name!r}. "
            f"Allowed tables: {sorted(ALLOWED_TABLES)}"
        )
    if not _IDENTIFIER_PATTERN.fullmatch(table_name):
        raise ValueError("table_name contains unsupported characters")


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    _check_table_name(table_name)
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone() is not None


def _require_table(conn: sqlite3.Connection, table_name: str) -> None:
    if not _table_exists(conn, table_name):
        raise ValueError(f"Table does not exist: {table_name}")


def register_student_course(
    conn: sqlite3.Connection,
    frame: pd.DataFrame,
    table_name: str = DEFAULT_TABLE,
    *,
    replace: bool = False,
) -> None:
    """Validate and register the student-course reporting table."""
    _check_connection(conn)
    _check_table_name(table_name)

    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame")

    missing = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(
            "student_course is missing required columns: " + ", ".join(missing)
        )

    validate_student_course_table(frame)

    if _table_exists(conn, table_name) and not replace:
        raise ValueError(
            f"Table already exists: {table_name}. "
            "Pass replace=True to replace it explicitly."
        )

    frame.to_sql(
        table_name,
        conn,
        if_exists="replace" if replace else "fail",
        index=False,
    )


def _run_sql_file(
    conn: sqlite3.Connection,
    filename: str,
    parameters: Sequence[object] = (),
) -> pd.DataFrame:
    _check_connection(conn)

    if isinstance(parameters, (str, bytes)) or not isinstance(parameters, Sequence):
        raise TypeError("parameters must be a sequence of SQL parameter values")

    path = SQL_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"SQL report file not found: {path}")

    query = path.read_text(encoding="utf-8").strip()
    if not query:
        raise ValueError(f"SQL report file is empty: {filename}")

    return pd.read_sql_query(query, conn, params=tuple(parameters))


def run_report(
    conn: sqlite3.Connection,
    report_name: str,
    parameters: Sequence[object] = (),
) -> pd.DataFrame:
    """Execute only repository-owned SELECT reports."""
    reports = {
        "overall_kpis": "sql_overall_kpis.sql",
        "course_performance": "sql_course_performance.sql",
        "behaviour_by_status": "sql_behaviour_by_status.sql",
        "segment_performance": "sql_segment_performance.sql",
    }

    if report_name not in reports:
        raise ValueError(
            f"Unknown report: {report_name!r}. "
            f"Available reports: {sorted(reports)}"
        )

    return _run_sql_file(conn, reports[report_name], parameters)


def overall_kpis(conn: sqlite3.Connection, table_name: str = DEFAULT_TABLE) -> pd.DataFrame:
    _check_table_name(table_name)
    _require_table(conn, table_name)
    return run_report(conn, "overall_kpis")


def course_performance(conn: sqlite3.Connection, table_name: str = DEFAULT_TABLE) -> pd.DataFrame:
    _check_table_name(table_name)
    _require_table(conn, table_name)
    return run_report(conn, "course_performance")


def behaviour_by_status(conn: sqlite3.Connection, table_name: str = DEFAULT_TABLE) -> pd.DataFrame:
    _check_table_name(table_name)
    _require_table(conn, table_name)
    return run_report(conn, "behaviour_by_status")


def segment_performance(conn: sqlite3.Connection, table_name: str = DEFAULT_TABLE) -> pd.DataFrame:
    _check_table_name(table_name)
    _require_table(conn, table_name)
    return run_report(conn, "segment_performance")
