WITH
transformed AS (
  SELECT
    CASE
      WHEN sale_type = 'W' THEN 'WHOLESALE'
      WHEN sale_type = 'R' THEN 'RETAIL'
      WHEN sale_type = 'O' THEN 'ONLINE'
      ELSE NULL
    END AS reference
  FROM sales
)
SELECT reference FROM transformed
