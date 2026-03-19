WITH
with_majors AS (
  SELECT s.student_id,
         CONCAT(s.first_name, ' ', s.last_name) AS student_name
  FROM students s
  LEFT JOIN majors m ON s.major_id = m.major_id
),
with_courses AS (
  SELECT e.student_id
  FROM enrollments e
  LEFT JOIN courses c ON e.course_id = c.course_id
),
combined AS (
  SELECT wm.student_name
  FROM with_majors wm
  LEFT JOIN with_courses wc ON wm.student_id = wc.student_id
)
SELECT student_name FROM combined
