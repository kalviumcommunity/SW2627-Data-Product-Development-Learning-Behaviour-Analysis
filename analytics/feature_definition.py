FEATURE_DEFINITIONS = {
    "total_study_hours": {
        "description": "Total learning session duration in hours",
        "source": "learning_sessions",
        "calculation": "sum(duration_minutes) / 60",
    },
    "avg_session_length": {
        "description": "Average learning session duration in minutes",
        "source": "learning_sessions",
        "calculation": "mean(duration_minutes)",
    },
    "quiz_accuracy": {
        "description": "Average quiz score percentage",
        "source": "quiz_performance",
        "calculation": "mean(score_pct)",
    },
    "active_days": {
        "description": "Number of distinct days with learning activity",
        "source": "learning_sessions",
        "calculation": "nunique(activity_date)",
    },
    "days_since_last_activity": {
        "description": "Days since the learner's most recent session",
        "source": "learning_sessions",
        "calculation": "current_date - max(start_time)",
    },
    "quiz_frequency": {
        "description": "Number of quiz attempts completed by a learner",
        "source": "quiz_performance",
        "calculation": "count(score_pct)",
    },
    "learning_streak": {
        "description": "Longest sequence of consecutive active learning days",
        "source": "learning_sessions",
        "calculation": "longest_consecutive_active_days",
    },
    "weekly_sessions": {
        "description": "Average number of learning sessions per week",
        "source": "learning_sessions",
        "calculation": "mean(sessions_per_week)",
    },
    "completion_pct": {
        "description": "Current percentage of the course completed by the learner",
        "source": "course_completion",
        "calculation": "completion_pct",
    },
}