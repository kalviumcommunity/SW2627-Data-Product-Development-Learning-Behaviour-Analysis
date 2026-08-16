def transform_sessions(df):
    return (
        df.groupby(["student_id", "course_id"])
        .agg(
            total_duration=("duration_minutes", "sum"),
            session_count=("duration_minutes", "size"),
        )
        .reset_index()
    )


def transform_quiz(df):
    return (
        df.groupby(["student_id", "course_id"])
        .agg(
            avg_quiz_score=("score_pct", "mean"),
            quiz_attempts=("attempt_number", "size"),
        )
        .reset_index()
    )