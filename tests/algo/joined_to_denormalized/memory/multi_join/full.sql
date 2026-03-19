WITH
with_majors AS (
  SELECT s.student_id,
         CONCAT(s.first_name, ' ', s.last_name) AS student_name,
         m.major_name AS major, m.department
  FROM students s
  LEFT JOIN majors m ON s.major_id = m.major_id
),
with_courses AS (
  SELECT e.student_id, e.grade, e.semester,
         c.course_name, c.credits
  FROM enrollments e
  LEFT JOIN courses c ON e.course_id = c.course_id
),
combined AS (
  SELECT wm.student_name, wm.major, wm.department,
         wc.course_name, wc.credits,
         CASE
           WHEN wc.grade = 'A' THEN 4.0 * wc.credits
           WHEN wc.grade = 'B' THEN 3.0 * wc.credits
           WHEN wc.grade = 'C' THEN 2.0 * wc.credits
           WHEN wc.grade = 'D' THEN 1.0 * wc.credits
           ELSE 0.0
         END AS grade_points,
         wc.semester
  FROM with_majors wm
  LEFT JOIN with_courses wc ON wm.student_id = wc.student_id
)
SELECT * FROM combined
