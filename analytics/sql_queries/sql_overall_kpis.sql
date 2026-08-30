SELECT
    COUNT(*) AS learner_course_count,
    COUNT(DISTINCT student_id) AS learner_count,
    COUNT(DISTINCT course_id) AS course_count,
    ROUND(AVG(completion_pct), 2) AS avg_completion_pct,
    ROUND(AVG(quiz_accuracy), 2) AS avg_quiz_accuracy,
    ROUND(AVG(total_study_hours), 2) AS avg_study_hours,
    ROUND(100.0 * SUM(CASE WHEN LOWER(TRIM(status)) = 'completed' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS completion_rate,
    ROUND(100.0 * SUM(CASE WHEN LOWER(TRIM(status)) = 'dropped' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS dropoff_rate
FROM student_course;
