-- LearnLens AI: course completion KPI query
-- Source: course_completion(student_id, course_id, enrollment_date, completion_pct, status)

SELECT
    course_id,
    COUNT(DISTINCT student_id) AS enrolled_students,
    COUNT(DISTINCT CASE WHEN status = 'completed' THEN student_id END) AS completed_students,
    COUNT(DISTINCT CASE WHEN status = 'dropped' THEN student_id END) AS dropped_students,
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN status = 'completed' THEN student_id END)
        / NULLIF(COUNT(DISTINCT student_id), 0),
        2
    ) AS completion_rate_pct,
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN status = 'dropped' THEN student_id END)
        / NULLIF(COUNT(DISTINCT student_id), 0),
        2
    ) AS dropoff_rate_pct
FROM course_completion
GROUP BY course_id
ORDER BY completion_rate_pct DESC, course_id;