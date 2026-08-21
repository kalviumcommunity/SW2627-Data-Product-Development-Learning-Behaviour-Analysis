"""Frontend-facing data access for LearnLens.

This service consumes the analytics that are currently available in the
repository's MVP data contract. It deliberately does not assume optional
timestamp/start-time fields that are not present in the current datasets.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from analytics.kpis import kpi_summary
from analytics.funnel import build_completion_funnel
from pipeline.clean import clean_completion, clean_quiz, clean_sessions
from pipeline.ingest import load_all_data


ALL_COURSES = "All Courses"
ALL_SEGMENTS = "All Segments"
ALL_STATUSES = "Any Status"


@dataclass(frozen=True)
class DashboardData:
    raw: dict[str, pd.DataFrame]


class AnalyticsService:
    """Application boundary between Streamlit views and existing analytics."""

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
        """Apply only filters supported by the current backend schema."""

        raw = {
            name: frame.copy()
            for name, frame in dashboard.raw.items()
        }

        if course != ALL_COURSES:
            for name, frame in raw.items():
                if "course_id" in frame.columns:
                    raw[name] = frame[
                        frame["course_id"].astype(str) == str(course)
                    ].copy()

        if status != ALL_STATUSES:
            for name, frame in raw.items():
                if "status" in frame.columns:
                    raw[name] = frame[
                        frame["status"]
                        .astype(str)
                        .str.lower()
                        .eq(status.lower())
                    ].copy()

        return DashboardData(raw=raw)

    def kpis(self, dashboard: DashboardData) -> dict[str, float | int]:
        return kpi_summary(
            completion_df=dashboard.raw["completion"],
            quiz_df=dashboard.raw["quiz"],
            sessions_df=dashboard.raw["sessions"],
        )

    def funnel(self, dashboard: DashboardData) -> pd.DataFrame:
        return build_completion_funnel(dashboard.raw["completion"])

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
