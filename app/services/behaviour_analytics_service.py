"""Frontend adapter for backend behavioural analytics.

Does not fabricate timestamps. If the current quiz data has no timestamp,
non-timestamp behavioural features are calculated from the canonical fields
already loaded by AnalyticsService, then the existing backend analytics
modules are reused.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

from app.services.analytics_service import AnalyticsService, DashboardData
from analytics.segmentation import segment_learners, segment_summary
from analytics.recommendations import generate_recommendations, recommendation_summary
from analytics.learner_insights import build_learner_insights, insight_summary
from analytics.relationship_analysis import correlate_with_completion, correlation_matrix
from analytics.root_cause import analyze_root_causes, root_cause_summary


class BehaviourAnalyticsService:
    def __init__(self, data_path: str | Path | None = None) -> None:
        self._dashboard_service = AnalyticsService(data_path=data_path)

    def load(self) -> DashboardData:
        return self._dashboard_service.load()

    @staticmethod
    def build_features(dashboard: DashboardData) -> pd.DataFrame:
        raw = dashboard.raw
        required = {"completion", "quiz", "sessions"}
        missing = sorted(required - set(raw))
        if missing:
            raise ValueError(f"Behaviour analytics requires datasets: {missing}")

        completion = raw["completion"].copy()
        quiz = raw["quiz"].copy()
        sessions = raw["sessions"].copy()
        keys = ["student_id", "course_id"]

        checks = (
            (completion, set(keys) | {"completion_pct", "status"}, "completion"),
            (quiz, set(keys) | {"score_pct"}, "quiz"),
            (sessions, set(keys) | {"duration_minutes"}, "sessions"),
        )
        for frame, required_cols, name in checks:
            missing_cols = sorted(required_cols - set(frame.columns))
            if missing_cols:
                raise ValueError(f"{name} data is missing required columns: {missing_cols}")

        # Use the canonical backend implementation whenever its timestamp
        # contract is available.
        if "timestamp" in quiz.columns and "enrollment" in raw:
            from analytics.feature_engineering import build_behavioural_features
            return build_behavioural_features(
                completion, quiz, sessions, raw["enrollment"]
            )

        # Safe fallback for the repository's current quiz schema. It does
        # not invent dates and therefore does not claim timestamp analytics.
        base = completion[keys + ["completion_pct", "status"]].drop_duplicates(
            keys, keep="last"
        ).copy()

        s = sessions.copy()
        s["duration_minutes"] = pd.to_numeric(s["duration_minutes"], errors="coerce")
        s = s.dropna(subset=keys + ["duration_minutes"])
        s = s[s["duration_minutes"] >= 0]

        if s.empty:
            sf = pd.DataFrame(columns=keys + [
                "total_study_hours", "avg_session_length", "active_days",
                "learning_streak", "days_since_last_activity", "weekly_sessions"
            ])
        else:
            sf = s.groupby(keys).agg(
                total_study_hours=("duration_minutes", lambda x: x.sum() / 60),
                avg_session_length=("duration_minutes", "mean"),
                active_days=("duration_minutes", "size"),
            ).reset_index()
            sf["learning_streak"] = 0.0
            sf["days_since_last_activity"] = 0.0
            sf["weekly_sessions"] = sf["active_days"].astype(float)

        q = quiz.copy()
        q["score_pct"] = pd.to_numeric(q["score_pct"], errors="coerce")
        q = q.dropna(subset=keys + ["score_pct"])
        q = q[q["score_pct"].between(0, 100)]

        if q.empty:
            qf = pd.DataFrame(columns=keys + ["quiz_accuracy", "quiz_frequency"])
        else:
            qf = q.groupby(keys).agg(
                quiz_accuracy=("score_pct", "mean"),
                quiz_frequency=("score_pct", "count"),
            ).reset_index()

        result = base.merge(sf, on=keys, how="left").merge(qf, on=keys, how="left")
        numeric = [
            "total_study_hours", "avg_session_length", "quiz_accuracy",
            "quiz_frequency", "active_days", "learning_streak",
            "days_since_last_activity", "weekly_sessions", "completion_pct"
        ]
        for column in numeric:
            result[column] = pd.to_numeric(result[column], errors="coerce").fillna(0.0)

        result["completion_pct"] = result["completion_pct"].clip(0, 100)
        result["cohort"] = pd.NA
        return result[
            ["student_id", "course_id", "cohort", "total_study_hours",
             "avg_session_length", "quiz_accuracy", "quiz_frequency",
             "active_days", "learning_streak", "days_since_last_activity",
             "weekly_sessions", "completion_pct", "status"]
        ].sort_values(keys).reset_index(drop=True)

    segments = staticmethod(segment_learners)
    segment_summary = staticmethod(segment_summary)
    recommendations = staticmethod(generate_recommendations)
    recommendation_summary = staticmethod(recommendation_summary)
    insights = staticmethod(build_learner_insights)
    insight_summary = staticmethod(insight_summary)
    relationships = staticmethod(correlate_with_completion)
    correlation_matrix = staticmethod(correlation_matrix)
    root_causes = staticmethod(analyze_root_causes)
    root_cause_summary = staticmethod(root_cause_summary)
