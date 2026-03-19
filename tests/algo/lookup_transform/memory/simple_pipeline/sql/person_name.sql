WITH
transformed AS (
  SELECT
    person_name
  FROM sales
)
SELECT person_name FROM transformed
