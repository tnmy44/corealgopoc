-- Source: deterministic match
WITH
with_customers AS (
  SELECT s.sale_date, s.product_id
  FROM sales s
  LEFT JOIN customers c ON s.customer_id = c.customer_id
),
with_products AS (
  SELECT wc.sale_date
  FROM with_customers wc
  LEFT JOIN products p ON wc.product_id = p.product_id
),
transformed AS (
  SELECT EXTRACT(YEAR FROM CAST(sale_date AS DATE)) AS sale_year
  FROM with_products
)
SELECT sale_year FROM transformed
