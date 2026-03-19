WITH
transformed AS (
  SELECT
    sale_id
  FROM sales
)
SELECT sale_id FROM transformed
