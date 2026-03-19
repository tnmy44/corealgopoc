WITH
with_customers AS (
  SELECT s.sale_id, s.product_id
  FROM sales s
  LEFT JOIN customers c ON s.customer_id = c.customer_id
),
with_products AS (
  SELECT wc.sale_id
  FROM with_customers wc
  LEFT JOIN products p ON wc.product_id = p.product_id
),
transformed AS (
  SELECT sale_id
  FROM with_products
)
SELECT sale_id FROM transformed
