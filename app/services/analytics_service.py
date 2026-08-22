"""Frontend-facing access to the existing analytics layer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from analytics.funnel import build_completion_funnel
from analytics.kpis import kpi_summary
from pipeline.clean import clean_completion, clean_quiz, clean_sessions
from pipeline.ingest import load_all_data


ALL_COURSES = "All Courses"
ALL_SEGMENTS = "All Segments"
ALL_STATUSES = "Any Status"


@dataclass(frozen=True)
class DashboardData:
    """Prepared source tables used by dashboard views."""

    raw: dict[str, pd.DataFrame]


class AnalyticsService:
    """Application boundary between Streamlit and existing analytics."""

    def __init__(self, data_path: str | Path = "data/raw") -> None:
        self.data_path = Path(data_path)

    def load(self) -> DashboardData:
        data = load_all_data(self.data_path)
        data["completion"] = clean_completion(data["completion"])
        data["quiz"] = clean_quiz(data["quiz"])
        data["sessions"] = clean_sessions(data["sessions"])
        return DashboardData(raw=data)

    @staticmethod
    def filter_data(
        dashboard: DashboardData,
        *,
        course: str = ALL_COURSES,
        status: str = ALL_STATUSES,
    ) -> DashboardData:
        """Filter all datasets using one canonical student-course population."""

        raw = {name: frame.copy() for name, frame in dashboard.raw.items()}
        keys = ["student_id", "course_id"]
        completion = raw["completion"]

        if not set(keys).issubset(completion.columns):
            return DashboardData(raw=raw)

        population = completion[keys].drop_duplicates()

        if course != ALL_COURSES:
            population = population[
                population["course_id"].astype(str) == str(course)
            ]

        if status != ALL_STATUSES and "status" in completion.columns:
            matching = completion[
                completion["status"].astype(str).str.lower().eq(status.lower())
            ]
            population = population.merge(
                matching[keys].drop_duplicates(),
                on=keys,
                how="inner",
            )

        for name, frame in raw.items():
            if set(keys).issubset(frame.columns):
                raw[name] = frame.merge(
                    population,
                    on=keys,
                    how="inner",
                )

        return DashboardData(raw=raw)

    def kpis(self, dashboard: DashboardData) -> dict[str, float | int]:
        return kpi_summary(
            completion_df=dashboard.raw["completion"],
            quiz_df=dashboard.raw["quiz"],
            sessions_df=dashboard.raw["sessions"],
        )

    def funnel(self, dashboard: DashboardData) -> pd.DataFrame:
        return build_completion_funnel(dashboard.raw["completion"])

    def behaviour_summary(self, dashboard: DashboardData) -> dict[str, float | int]:
        """Calculate behavioural metrics supported by the current MVP schema."""

        completion = dashboard.raw["completion"]
        quiz = dashboard.raw["quiz"]
        sessions = dashboard.raw["sessions"]

        if completion.empty:
            return {
                "avg_study_time_hours": 0.0,
                "avg_sessions": 0.0,
                "avg_quiz_attempts": 0.0,
                "completion_rate": 0.0,
                "learner_count": 0,
            }

        duration = pd.to_numeric(
            sessions.get("duration_minutes", pd.Series(dtype=float)),
            errors="coerce",
        )
        avg_study_time_hours = (
            float(duration.mean() / 60)
            if not duration.dropna().empty
            else 0.0
        )

        session_counts = (
            sessions.groupby(["student_id", "course_id"]).size()
            if {"student_id", "course_id"}.issubset(sessions.columns)
            else pd.Series(dtype=float)
        )
        avg_sessions = (
            float(session_counts.mean()) if not session_counts.empty else 0.0
        )

        attempts = pd.to_numeric(
            quiz.get("attempt_number", pd.Series(dtype=float)),
            errors="coerce",
        )
        avg_quiz_attempts = (
            float(attempts.mean()) if not attempts.dropna().empty else 0.0
        )

        completion_pct = pd.to_numeric(
            completion.get("completion_pct", pd.Series(dtype=float)),
            errors="coerce",
        )
        completion_rate = (
            float(completion_pct.ge(100).mean() * 100)
            if not completion_pct.dropna().empty
            else 0.0
        )

        learner_count = (
            int(completion["student_id"].nunique())
            if "student_id" in completion.columns
            else 0
        )

        return {
            "avg_study_time_hours": round(avg_study_time_hours, 2),
            "avg_sessions": round(avg_sessions, 2),
            "avg_quiz_attempts": round(avg_quiz_attempts, 2),
            "completion_rate": round(completion_rate, 1),
            "learner_count": learner_count,
        }

    def behaviour_by_status(self, dashboard: DashboardData) -> pd.DataFrame:
        """Compare available behaviour metrics across completion statuses."""

        completion = dashboard.raw["completion"].copy()
        quiz = dashboard.raw["quiz"].copy()
        sessions = dashboard.raw["sessions"].copy()

        if completion.empty:
            return pd.DataFrame(
                columns=[
                    "status",
                    "learners",
                    "avg_completion_pct",
                    "avg_quiz_score",
                    "avg_quiz_attempts",
                    "avg_study_hours",
                    "avg_sessions",
                ]
            )

        if {"student_id", "course_id"}.issubset(quiz.columns):
            quiz_summary = (
                quiz.groupby(["student_id", "course_id"], as_index=False)
                .agg(
                    avg_quiz_score=("score_pct", "mean"),
                    avg_quiz_attempts=("attempt_number", "mean"),
                )
            )
        else:
            quiz_summary = pd.DataFrame(
                columns=[
                    "student_id",
                    "course_id",
                    "avg_quiz_score",
                    "avg_quiz_attempts",
                ]
            )

        if {
            "student_id",
            "course_id",
            "duration_minutes",
        }.issubset(sessions.columns):
            session_data = sessions.copy()
            session_data["duration_minutes"] = pd.to_numeric(
                session_data["duration_minutes"],
                errors="coerce",
            )
            session_summary = (
                session_data.groupby(
                    ["student_id", "course_id"],
                    as_index=False,
                )
                .agg(
                    total_minutes=("duration_minutes", "sum"),
                    sessions=("duration_minutes", "size"),
                )
            )
        else:
            session_summary = pd.DataFrame(
                columns=[
                    "student_id",
                    "course_id",
                    "total_minutes",
                    "sessions",
                ]
            )

        merged = completion.merge(
            quiz_summary,
            on=["student_id", "course_id"],
            how="left",
        ).merge(
            session_summary,
            on=["student_id", "course_id"],
            how="left",
        )

        summary = (
            merged.groupby("status", dropna=False)
            .agg(
                learners=("student_id", "nunique"),
                avg_completion_pct=("completion_pct", "mean"),
                avg_quiz_score=("avg_quiz_score", "mean"),
                avg_quiz_attempts=("avg_quiz_attempts", "mean"),
                avg_study_hours=("total_minutes", lambda x: x.mean() / 60),
                avg_sessions=("sessions", "mean"),
            )
            .reset_index()
        )

        return summary.round(
            {
                "avg_completion_pct": 2,
                "avg_quiz_score": 2,
                "avg_quiz_attempts": 2,
                "avg_study_hours": 2,
                "avg_sessions": 2,
            }
        )

    @staticmethod
    def course_options(dashboard: DashboardData) -> list[str]:
        completion = dashboard.raw["completion"]
        if "course_id" not in completion.columns:
            return [ALL_COURSES]

        courses = (
            completion["course_id"]
            .dropna()
            .astype(str)
            .drop_duplicates()
            .sort_values()
            .tolist()
        )
        return [ALL_COURSES, *courses]
