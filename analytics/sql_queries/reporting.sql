-- SQLite-compatible reporting queries over student_course.
SELECT
    COUNT(*) AS learner_course_count,
    COUNT(DISTINCT student_id) AS learner_count,
    COUNT(DISTINCT course_id) AS course_count,
    ROUND(AVG(completion_pct), 2) AS avg_completion_pct,
    ROUND(AVG(quiz_accuracy), 2) AS avg_quiz_accuracy,
    ROUND(AVG(total_study_hours), 2) AS avg_study_hours,
    ROUND(100.0 * SUM(CASE WHEN LOWER(TRIM(status))='completed' THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 2) AS completion_rate,
    ROUND(100.0 * SUM(CASE WHEN LOWER(TRIM(status))='dropped' THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 2) AS dropoff_rate
FROM student_course;

SELECT
    course_id,
    COUNT(*) AS learner_count,
    SUM(CASE WHEN LOWER(TRIM(status))='completed' THEN 1 ELSE 0 END) AS completed_count,
    SUM(CASE WHEN LOWER(TRIM(status))='dropped' THEN 1 ELSE 0 END) AS dropped_count,
    ROUND(AVG(completion_pct),2) AS avg_completion_pct,
    ROUND(100.0 * SUM(CASE WHEN LOWER(TRIM(status))='completed' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) AS completion_rate,
    ROUND(100.0 * SUM(CASE WHEN LOWER(TRIM(status))='dropped' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) AS dropoff_rate,
    ROUND(AVG(quiz_accuracy),2) AS avg_quiz_accuracy,
    ROUND(AVG(total_study_hours),2) AS avg_study_hours
FROM student_course
GROUP BY course_id
ORDER BY course_id;

SELECT
    LOWER(TRIM(status)) AS status,
    COUNT(*) AS learner_count,
    ROUND(AVG(completion_pct),2) AS avg_completion_pct,
    ROUND(AVG(quiz_accuracy),2) AS avg_quiz_accuracy,
    ROUND(AVG(total_study_hours),2) AS avg_study_hours,
    ROUND(AVG(active_days),2) AS avg_active_days,
    ROUND(AVG(learning_streak),2) AS avg_learning_streak,
    ROUND(AVG(days_since_last_activity),2) AS avg_days_since_last_activity,
    ROUND(AVG(weekly_sessions),2) AS avg_weekly_sessions
FROM student_course
GROUP BY LOWER(TRIM(status))
ORDER BY status;

SELECT
    segment,
    COUNT(*) AS learner_count,
    ROUND(AVG(completion_pct),2) AS avg_completion_pct,
    ROUND(AVG(quiz_accuracy),2) AS avg_quiz_accuracy,
    ROUND(AVG(total_study_hours),2) AS avg_study_hours,
    ROUND(AVG(days_since_last_activity),2) AS avg_days_since_last_activity,
    SUM(CASE WHEN LOWER(TRIM(status))='completed' THEN 1 ELSE 0 END) AS completed_count,
    SUM(CASE WHEN LOWER(TRIM(status))='dropped' THEN 1 ELSE 0 END) AS dropped_count
FROM student_course
GROUP BY segment
ORDER BY learner_count DESC, segment;
