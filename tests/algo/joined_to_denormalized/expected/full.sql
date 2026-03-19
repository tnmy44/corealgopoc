-- Source: deterministic match from multi_join (adapted: all JOINs removed, denormalized source)
SELECT student_name, major, department, course_name, credits, grade_points, semester
FROM student_records
