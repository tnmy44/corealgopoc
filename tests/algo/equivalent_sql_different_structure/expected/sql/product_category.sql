-- Source: deterministic match
WITH
with_customers AS (
  SELECT s.product_id
  FROM sales s
  LEFT JOIN customers c ON s.customer_id = c.customer_id
),
with_products AS (
  SELECT p.category AS product_category
  FROM with_customers wc
  LEFT JOIN products p ON wc.product_id = p.product_id
),
transformed AS (
  SELECT product_category
  FROM with_products
)
SELECT product_category FROM transformed
