"""Behavioural feature engineering for LearnLens AI PR 2."""
from __future__ import annotations

import pandas as pd


def _require(df: pd.DataFrame, cols: list[str], name: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def _streak(dates: pd.Series) -> int:
    dates = pd.to_datetime(dates, errors="coerce").dropna().dt.normalize().drop_duplicates().sort_values()
    if dates.empty:
        return 0
    groups = dates.diff().dt.days.fillna(1).ne(1).cumsum()
    return int(dates.groupby(groups).size().max())


def build_behavioural_features(
    completion_df: pd.DataFrame,
    quiz_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    enrollment_df: pd.DataFrame,
    reference_date: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Create one student-course row containing behavioural features.

    Features: total_study_hours, avg_session_length, quiz_accuracy,
    quiz_frequency, active_days, learning_streak, days_since_last_activity,
    weekly_sessions, completion_pct, status, and cohort.
    """
    _require(completion_df, ["student_id", "course_id", "completion_pct", "status"], "completion_df")
    _require(quiz_df, ["student_id", "course_id", "score_pct", "timestamp"], "quiz_df")
    _require(sessions_df, ["student_id", "course_id", "start_time", "duration_minutes"], "sessions_df")
    _require(enrollment_df, ["student_id", "course_id"], "enrollment_df")

    ref = pd.Timestamp.today().normalize() if reference_date is None else pd.Timestamp(reference_date).normalize()

    base_cols = ["student_id", "course_id"] + (["cohort"] if "cohort" in enrollment_df else [])
    base = enrollment_df[base_cols].drop_duplicates(["student_id", "course_id"]).copy()
    if "cohort" not in base:
        base["cohort"] = pd.NA

    completion = completion_df[["student_id", "course_id", "completion_pct", "status"]].copy()
    completion["completion_pct"] = pd.to_numeric(completion["completion_pct"], errors="coerce").clip(0, 100)
    completion = completion.drop_duplicates(["student_id", "course_id"], keep="last")
    base = base.merge(completion, on=["student_id", "course_id"], how="left")

    sessions = sessions_df.copy()
    sessions["start_time"] = pd.to_datetime(sessions["start_time"], errors="coerce")
    sessions["duration_minutes"] = pd.to_numeric(sessions["duration_minutes"], errors="coerce")
    sessions = sessions.dropna(subset=["student_id", "course_id", "start_time", "duration_minutes"])
    sessions = sessions[sessions["duration_minutes"] >= 0]

    if sessions.empty:
        sf = pd.DataFrame(columns=["student_id","course_id","total_study_hours","avg_session_length","active_days","learning_streak","days_since_last_activity","weekly_sessions"])
    else:
        sf = sessions.groupby(["student_id","course_id"]).agg(
            total_study_hours=("duration_minutes", lambda x: x.sum()/60),
            avg_session_length=("duration_minutes", "mean"),
            active_days=("start_time", lambda x: x.dt.normalize().nunique()),
            last_activity=("start_time", "max"),
        ).reset_index()
        streaks = sessions.groupby(["student_id","course_id"])["start_time"].apply(_streak).reset_index(name="learning_streak")
        weekly = (sessions.assign(week=sessions["start_time"].dt.to_period("W"))
                  .groupby(["student_id","course_id","week"]).size()
                  .groupby(["student_id","course_id"]).mean()
                  .reset_index(name="weekly_sessions"))
        sf = sf.merge(streaks, on=["student_id","course_id"]).merge(weekly, on=["student_id","course_id"])
        sf["days_since_last_activity"] = (ref - sf["last_activity"].dt.normalize()).dt.days.clip(lower=0)
        sf = sf.drop(columns="last_activity")

    quizzes = quiz_df.copy()
    quizzes["timestamp"] = pd.to_datetime(quizzes["timestamp"], errors="coerce")
    quizzes["score_pct"] = pd.to_numeric(quizzes["score_pct"], errors="coerce")
    quizzes = quizzes.dropna(subset=["student_id","course_id","score_pct","timestamp"])
    quizzes = quizzes[quizzes["score_pct"].between(0, 100)]
    if quizzes.empty:
        qf = pd.DataFrame(columns=["student_id","course_id","quiz_accuracy","quiz_frequency"])
    else:
        qf = quizzes.groupby(["student_id","course_id"]).agg(
            quiz_accuracy=("score_pct","mean"),
            quiz_frequency=("score_pct","count"),
        ).reset_index()

    result = base.merge(sf, on=["student_id","course_id"], how="left").merge(qf, on=["student_id","course_id"], how="left")
    numeric = ["total_study_hours","avg_session_length","quiz_accuracy","quiz_frequency","active_days","learning_streak","days_since_last_activity","weekly_sessions"]
    for col in numeric:
        result[col] = pd.to_numeric(result[col], errors="coerce").fillna(0.0)
    result["completion_pct"] = pd.to_numeric(result["completion_pct"], errors="coerce").fillna(0.0).clip(0, 100)
    return result[["student_id","course_id","cohort","total_study_hours","avg_session_length","quiz_accuracy","quiz_frequency","active_days","learning_streak","days_since_last_activity","weekly_sessions","completion_pct","status"]].sort_values(["course_id","student_id"]).reset_index(drop=True)
