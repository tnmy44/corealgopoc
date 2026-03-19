WITH
salaried AS (
  SELECT emp_id, name, annual_salary / 12.0 AS monthly_pay, dept AS department
  FROM salaried_employees
),
hourly AS (
  SELECT emp_id, name, hourly_rate * hours_per_week * 4.33 AS monthly_pay, dept AS department
  FROM hourly_employees
),
combined AS (
  SELECT * FROM salaried
  UNION ALL
  SELECT * FROM hourly
)
SELECT * FROM combined
