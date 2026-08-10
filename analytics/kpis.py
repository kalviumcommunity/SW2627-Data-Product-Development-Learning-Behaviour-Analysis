from __future__ import annotations

import pandas as pd


def _require_columns(df: pd.DataFrame, columns: list[str]) -> None:
    """Raise ValueError when required columns are missing."""
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def completion_rate(df: pd.DataFrame) -> float:
    """Return the percentage of records with status='completed'."""
    _require_columns(df, ["status"])
    if df.empty:
        return 0.0
    return float(df["status"].eq("completed").mean() * 100)


def dropoff_rate(df: pd.DataFrame) -> float:
    """Return the percentage of records with status='dropped'."""
    _require_columns(df, ["status"])
    if df.empty:
        return 0.0
    return float(df["status"].eq("dropped").mean() * 100)


def average_quiz_score(df: pd.DataFrame) -> float:
    """Return the mean quiz score percentage."""
    _require_columns(df, ["score_pct"])
    if df.empty:
        return 0.0
    mean_score = pd.to_numeric(df["score_pct"], errors="coerce").mean()
    return 0.0 if pd.isna(mean_score) else float(mean_score)


def active_student_count(df: pd.DataFrame) -> int:
    """Return the number of unique students with activity."""
    _require_columns(df, ["student_id"])
    if df.empty:
        return 0
    return int(df["student_id"].dropna().nunique())


def kpi_summary(completion_df, quiz_df, sessions_df) -> dict[str, float | int]:
    """Return the core LearnLens KPI set."""
    return {
        "completion_rate": completion_rate(completion_df),
        "dropoff_rate": dropoff_rate(completion_df),
        "average_quiz_score": average_quiz_score(quiz_df),
        "active_students": active_student_count(sessions_df),
    }