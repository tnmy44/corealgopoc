-- Source: deterministic match
WITH
with_customers AS (
  SELECT c.region, s.product_id
  FROM sales s
  LEFT JOIN customers c ON s.customer_id = c.customer_id
),
with_products AS (
  SELECT wc.region
  FROM with_customers wc
  LEFT JOIN products p ON wc.product_id = p.product_id
),
transformed AS (
  SELECT region
  FROM with_products
)
SELECT region FROM transformed
