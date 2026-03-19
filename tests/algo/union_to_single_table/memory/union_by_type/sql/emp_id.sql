WITH
salaried AS (
  SELECT emp_id FROM salaried_employees
),
hourly AS (
  SELECT emp_id FROM hourly_employees
),
combined AS (
  SELECT * FROM salaried
  UNION ALL
  SELECT * FROM hourly
)
SELECT emp_id FROM combined
