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
        self._validate_completion_grain(data["completion"])
        return DashboardData(raw=data)

    @staticmethod
    def _validate_completion_grain(completion: pd.DataFrame) -> None:
        required = {"student_id", "course_id"}
        missing = required.difference(completion.columns)
        if missing:
            raise ValueError(
                "completion data is missing required columns: "
                f"{sorted(missing)}"
            )

        if completion.duplicated(
            subset=["student_id", "course_id"],
            keep=False,
        ).any():
            raise ValueError(
                "completion data must contain one row per "
                "student-course pair."
            )

    @staticmethod
    def filter_data(
        dashboard: DashboardData,
        *,
        course: str = ALL_COURSES,
        status: str = ALL_STATUSES,
    ) -> DashboardData:
        raw = {name: frame.copy() for name, frame in dashboard.raw.items()}
        keys = ["student_id", "course_id"]
        completion = raw["completion"]

        AnalyticsService._validate_completion_grain(completion)

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

    def behaviour_summary(
        self,
        dashboard: DashboardData,
    ) -> dict[str, float | int]:
        """Calculate learner-course behavioural metrics."""

        completion = dashboard.raw["completion"]
        quiz = dashboard.raw["quiz"]
        sessions = dashboard.raw["sessions"]

        self._validate_completion_grain(completion)

        if completion.empty:
            return {
                "avg_study_time_hours": 0.0,
                "avg_sessions": 0.0,
                "avg_quiz_attempts": 0.0,
                "completion_rate": 0.0,
            }

        # Aggregate sessions to student-course first. This makes the
        # study-time KPI mean average total study time per learner-course.
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

            session_totals = (
                session_data.groupby(
                    ["student_id", "course_id"],
                    as_index=False,
                )
                .agg(
                    total_minutes=("duration_minutes", "sum"),
                    sessions=("duration_minutes", "size"),
                )
            )

            avg_study_time_hours = (
                float(session_totals["total_minutes"].mean() / 60)
                if not session_totals.empty
                else 0.0
            )
            avg_sessions = (
                float(session_totals["sessions"].mean())
                if not session_totals.empty
                else 0.0
            )
        else:
            avg_study_time_hours = 0.0
            avg_sessions = 0.0

        attempts = pd.to_numeric(
            quiz.get("attempt_number", pd.Series(dtype=float)),
            errors="coerce",
        )
        avg_quiz_attempts = (
            float(attempts.mean())
            if not attempts.dropna().empty
            else 0.0
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

        return {
            "avg_study_time_hours": round(avg_study_time_hours, 2),
            "avg_sessions": round(avg_sessions, 2),
            "avg_quiz_attempts": round(avg_quiz_attempts, 2),
            "completion_rate": round(completion_rate, 1),
        }

    def behaviour_by_status(
        self,
        dashboard: DashboardData,
    ) -> pd.DataFrame:
        """Compare behaviour metrics across completion statuses."""

        completion = dashboard.raw["completion"].copy()
        quiz = dashboard.raw["quiz"].copy()
        sessions = dashboard.raw["sessions"].copy()

        self._validate_completion_grain(completion)

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
            quiz_data = quiz.copy()
            quiz_data["score_pct"] = pd.to_numeric(
                quiz_data["score_pct"], errors="coerce"
            )
            if "attempt_number" in quiz_data.columns:
                quiz_data["attempt_number"] = pd.to_numeric(
                    quiz_data["attempt_number"],
                    errors="coerce",
                )
            else:
                quiz_data["attempt_number"] = pd.NA
            quiz_summary = (
                quiz_data.groupby(
                    ["student_id", "course_id"],
                    as_index=False,
                )
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
                session_data["duration_minutes"], errors="coerce"
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
            validate="one_to_one",
        ).merge(
            session_summary,
            on=["student_id", "course_id"],
            how="left",
            validate="one_to_one",
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


    # ============================================================
    # REPORTS & INSIGHTS
    # ============================================================

    def report_snapshot(
        self,
        dashboard: DashboardData,
    ) -> dict[str, float | int]:
        """Return report-level metrics for the selected population."""

        completion = dashboard.raw["completion"]

        if completion.empty:
            return {
                "records": 0,
                "courses": 0,
                "completion_rate": 0.0,
                "dropout_rate": 0.0,
                "average_quiz_score": 0.0,
                "active_students": 0,
                "avg_study_time_hours": 0.0,
            }

        kpis = self.kpis(dashboard)
        behaviour = self.behaviour_summary(dashboard)

        return {
            "records": int(len(completion)),
            "courses": int(
                completion["course_id"].dropna().nunique()
            ),
            "completion_rate": float(
                kpis.get("completion_rate", 0.0)
            ),
            "dropout_rate": float(
                kpis.get("dropoff_rate", 0.0)
            ),
            "average_quiz_score": float(
                kpis.get("average_quiz_score", 0.0)
            ),
            "active_students": int(
                kpis.get("active_students", 0)
            ),
            "avg_study_time_hours": float(
                behaviour.get(
                    "avg_study_time_hours",
                    0.0,
                )
            ),
        }

    def status_distribution(
        self,
        dashboard: DashboardData,
    ) -> pd.DataFrame:
        """Return learner counts by normalized completion status."""

        completion = dashboard.raw["completion"]

        columns = [
            "status",
            "learners",
            "percentage",
        ]

        if (
            completion.empty
            or "status" not in completion.columns
        ):
            return pd.DataFrame(columns=columns)

        statuses = (
            completion["status"]
            .astype("string")
            .str.strip()
            .str.lower()
            .str.replace(
                " ",
                "_",
                regex=False,
            )
        )

        result = (
            pd.DataFrame(
                {"status": statuses}
            )
            .groupby(
                "status",
                dropna=False,
            )
            .size()
            .reset_index(
                name="learners"
            )
        )

        total = int(
            result["learners"].sum()
        )

        if total:
            result["percentage"] = (
                result["learners"]
                / total
                * 100
            ).round(2)
        else:
            result["percentage"] = 0.0

        return (
            result[columns]
            .sort_values(
                "learners",
                ascending=False,
            )
            .reset_index(drop=True)
        )

    def report_export_data(
        self,
        dashboard: DashboardData,
    ) -> pd.DataFrame:
        """Return a stable learner-course report export."""

        completion = dashboard.raw[
            "completion"
        ].copy()

        columns = [
            "student_id",
            "course_id",
            "status",
            "completion_pct",
        ]

        if completion.empty:
            return pd.DataFrame(
                columns=columns
            )

        available = [
            column
            for column in columns
            if column in completion.columns
        ]

        export_data = completion[
            available
        ].copy()

        if "status" in export_data.columns:
            export_data["status"] = (
                export_data["status"]
                .astype("string")
                .str.strip()
                .str.lower()
                .str.replace(
                    " ",
                    "_",
                    regex=False,
                )
            )

        if "completion_pct" in export_data.columns:
            export_data[
                "completion_pct"
            ] = pd.to_numeric(
                export_data[
                    "completion_pct"
                ],
                errors="coerce",
            ).round(2)

        return export_data.reset_index(
            drop=True
        )

    # ============================================================
    # COURSE PERFORMANCE
    # ============================================================

    def course_performance(
        self,
        dashboard: DashboardData,
    ) -> pd.DataFrame:
        """Return one row per course for Course Performance."""

        completion = dashboard.raw["completion"].copy()
        quiz = dashboard.raw["quiz"].copy()
        sessions = dashboard.raw["sessions"].copy()

        self._validate_completion_grain(completion)

        columns = [
            "course_id",
            "learners",
            "completion_rate",
            "dropout_rate",
            "avg_completion_pct",
            "avg_quiz_score",
            "study_hours",
            "sessions",
            "active_students",
        ]

        if completion.empty:
            return pd.DataFrame(columns=columns)

        # Completion is guaranteed to be one row per student-course pair.
        completion["completion_pct"] = pd.to_numeric(
            completion.get(
                "completion_pct",
                pd.Series(index=completion.index, dtype=float),
            ),
            errors="coerce",
        )

        if "status" in completion.columns:
            completion["status_normalized"] = (
                completion["status"]
                .astype("string")
                .str.strip()
                .str.lower()
                .str.replace(" ", "_", regex=False)
            )
        else:
            completion["status_normalized"] = pd.Series(
                "",
                index=completion.index,
                dtype="string",
            )

        result = (
            completion.groupby(
                "course_id",
                as_index=False,
            )
            .agg(
                learners=("student_id", "nunique"),
                completion_rate=(
                    "status_normalized",
                    lambda values: values.eq("completed").mean() * 100,
                ),
                dropout_rate=(
                    "status_normalized",
                    lambda values: values.eq("dropped").mean() * 100,
                ),
                avg_completion_pct=(
                    "completion_pct",
                    "mean",
                ),
            )
        )

        # Quiz metrics are aggregated independently at course grain
        # before being joined, preventing join multiplication.
        if {
            "course_id",
            "score_pct",
        }.issubset(quiz.columns):
            quiz_data = quiz.copy()
            quiz_data["score_pct"] = pd.to_numeric(
                quiz_data["score_pct"],
                errors="coerce",
            )

            quiz_metrics = (
                quiz_data.groupby(
                    "course_id",
                    as_index=False,
                )
                .agg(
                    avg_quiz_score=(
                        "score_pct",
                        "mean",
                    )
                )
            )

            result = result.merge(
                quiz_metrics,
                on="course_id",
                how="left",
                validate="one_to_one",
            )
        else:
            result["avg_quiz_score"] = 0.0

        # Session metrics are aggregated at course grain.
        if {
            "course_id",
            "student_id",
            "duration_minutes",
        }.issubset(sessions.columns):
            session_data = sessions.copy()
            session_data["duration_minutes"] = pd.to_numeric(
                session_data["duration_minutes"],
                errors="coerce",
            )

            session_metrics = (
                session_data.groupby(
                    "course_id",
                    as_index=False,
                )
                .agg(
                    total_minutes=(
                        "duration_minutes",
                        "sum",
                    ),
                    sessions=(
                        "duration_minutes",
                        "size",
                    ),
                    active_students=(
                        "student_id",
                        "nunique",
                    ),
                )
            )

            session_metrics["study_hours"] = (
                session_metrics["total_minutes"] / 60
            )

            result = result.merge(
                session_metrics[
                    [
                        "course_id",
                        "study_hours",
                        "sessions",
                        "active_students",
                    ]
                ],
                on="course_id",
                how="left",
                validate="one_to_one",
            )
        else:
            result["study_hours"] = 0.0
            result["sessions"] = 0
            result["active_students"] = 0

        numeric_columns = [
            "learners",
            "completion_rate",
            "dropout_rate",
            "avg_completion_pct",
            "avg_quiz_score",
            "study_hours",
            "sessions",
            "active_students",
        ]

        for column in numeric_columns:
            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            ).fillna(0)

        return (
            result[columns]
            .round(
                {
                    "completion_rate": 2,
                    "dropout_rate": 2,
                    "avg_completion_pct": 2,
                    "avg_quiz_score": 2,
                    "study_hours": 2,
                }
            )
            .sort_values(
                ["completion_rate", "avg_quiz_score"],
                ascending=[False, False],
            )
            .reset_index(drop=True)
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
