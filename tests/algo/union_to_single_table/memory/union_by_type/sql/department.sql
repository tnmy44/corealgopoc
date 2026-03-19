WITH
salaried AS (
  SELECT dept AS department FROM salaried_employees
),
hourly AS (
  SELECT dept AS department FROM hourly_employees
),
combined AS (
  SELECT * FROM salaried
  UNION ALL
  SELECT * FROM hourly
)
SELECT department FROM combined
