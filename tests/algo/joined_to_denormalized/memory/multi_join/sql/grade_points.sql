WITH
with_majors AS (
  SELECT s.student_id
  FROM students s
  LEFT JOIN majors m ON s.major_id = m.major_id
),
with_courses AS (
  SELECT e.student_id, e.grade, c.credits
  FROM enrollments e
  LEFT JOIN courses c ON e.course_id = c.course_id
),
combined AS (
  SELECT
    CASE
      WHEN wc.grade = 'A' THEN 4.0 * wc.credits
      WHEN wc.grade = 'B' THEN 3.0 * wc.credits
      WHEN wc.grade = 'C' THEN 2.0 * wc.credits
      WHEN wc.grade = 'D' THEN 1.0 * wc.credits
      ELSE 0.0
    END AS grade_points
  FROM with_majors wm
  LEFT JOIN with_courses wc ON wm.student_id = wc.student_id
)
SELECT grade_points FROM combined
