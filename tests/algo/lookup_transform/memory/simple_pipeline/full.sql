WITH
transformed AS (
  SELECT
    sale_id,
    person_name,
    CASE
      WHEN sale_type = 'W' THEN 'WHOLESALE'
      WHEN sale_type = 'R' THEN 'RETAIL'
      WHEN sale_type = 'O' THEN 'ONLINE'
      ELSE NULL
    END AS reference
  FROM sales
)
SELECT sale_id, person_name, reference FROM transformed
