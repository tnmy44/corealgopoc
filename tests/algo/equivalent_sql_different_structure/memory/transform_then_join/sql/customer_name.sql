WITH
sales_computed AS (
  SELECT product_id, customer_id
  FROM sales
),
with_products AS (
  SELECT sc.customer_id
  FROM sales_computed sc
  LEFT JOIN products p ON sc.product_id = p.product_id
),
with_customers AS (
  SELECT c.customer_name
  FROM with_products wp
  LEFT JOIN customers c ON wp.customer_id = c.customer_id
)
SELECT customer_name FROM with_customers
