SELECT
    segment,
    COUNT(*) AS learner_count,
    ROUND(AVG(completion_pct), 2) AS avg_completion_pct,
    ROUND(AVG(quiz_accuracy), 2) AS avg_quiz_accuracy,
    ROUND(AVG(total_study_hours), 2) AS avg_study_hours,
    ROUND(AVG(days_since_last_activity), 2) AS avg_days_since_last_activity,
    SUM(CASE WHEN LOWER(TRIM(status)) = 'completed' THEN 1 ELSE 0 END) AS completed_count,
    SUM(CASE WHEN LOWER(TRIM(status)) = 'dropped' THEN 1 ELSE 0 END) AS dropped_count
FROM student_course
GROUP BY segment
ORDER BY learner_count DESC, segment;
