SELECT
    COALESCE(NULLIF(LOWER(TRIM(status)), ''), 'unknown') AS status,
    COUNT(*) AS learner_count,
    ROUND(AVG(completion_pct), 2) AS avg_completion_pct,
    ROUND(AVG(quiz_accuracy), 2) AS avg_quiz_accuracy,
    ROUND(AVG(total_study_hours), 2) AS avg_study_hours,
    ROUND(AVG(active_days), 2) AS avg_active_days,
    ROUND(AVG(learning_streak), 2) AS avg_learning_streak,
    ROUND(AVG(days_since_last_activity), 2) AS avg_days_since_last_activity,
    ROUND(AVG(weekly_sessions), 2) AS avg_weekly_sessions
FROM student_course
GROUP BY COALESCE(NULLIF(LOWER(TRIM(status)), ''), 'unknown')
ORDER BY status;
