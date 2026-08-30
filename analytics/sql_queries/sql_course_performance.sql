SELECT
    course_id,
    COUNT(*) AS learner_count,
    SUM(CASE WHEN LOWER(TRIM(status)) = 'completed' THEN 1 ELSE 0 END) AS completed_count,
    SUM(CASE WHEN LOWER(TRIM(status)) = 'dropped' THEN 1 ELSE 0 END) AS dropped_count,
    ROUND(AVG(completion_pct), 2) AS avg_completion_pct,
    ROUND(100.0 * SUM(CASE WHEN LOWER(TRIM(status)) = 'completed' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS completion_rate,
    ROUND(100.0 * SUM(CASE WHEN LOWER(TRIM(status)) = 'dropped' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS dropoff_rate,
    ROUND(AVG(quiz_accuracy), 2) AS avg_quiz_accuracy,
    ROUND(AVG(total_study_hours), 2) AS avg_study_hours
FROM student_course
GROUP BY course_id
ORDER BY course_id;
