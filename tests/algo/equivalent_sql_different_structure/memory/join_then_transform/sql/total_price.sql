WITH
with_customers AS (
  SELECT s.quantity, s.unit_price, s.product_id
  FROM sales s
  LEFT JOIN customers c ON s.customer_id = c.customer_id
),
with_products AS (
  SELECT wc.quantity, wc.unit_price
  FROM with_customers wc
  LEFT JOIN products p ON wc.product_id = p.product_id
),
transformed AS (
  SELECT quantity * unit_price AS total_price
  FROM with_products
)
SELECT total_price FROM transformed
