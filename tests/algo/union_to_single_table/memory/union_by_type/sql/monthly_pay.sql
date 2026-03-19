WITH
salaried AS (
  SELECT annual_salary / 12.0 AS monthly_pay FROM salaried_employees
),
hourly AS (
  SELECT hourly_rate * hours_per_week * 4.33 AS monthly_pay FROM hourly_employees
),
combined AS (
  SELECT * FROM salaried
  UNION ALL
  SELECT * FROM hourly
)
SELECT monthly_pay FROM combined
