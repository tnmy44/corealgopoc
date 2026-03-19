WITH
salaried AS (
  SELECT name FROM salaried_employees
),
hourly AS (
  SELECT name FROM hourly_employees
),
combined AS (
  SELECT * FROM salaried
  UNION ALL
  SELECT * FROM hourly
)
SELECT name FROM combined
