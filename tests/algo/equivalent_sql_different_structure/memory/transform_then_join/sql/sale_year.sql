WITH
sales_computed AS (
  SELECT product_id, customer_id,
         EXTRACT(YEAR FROM CAST(sale_date AS DATE)) AS sale_year
  FROM sales
),
with_products AS (
  SELECT sc.sale_year, sc.customer_id
  FROM sales_computed sc
  LEFT JOIN products p ON sc.product_id = p.product_id
),
with_customers AS (
  SELECT wp.sale_year
  FROM with_products wp
  LEFT JOIN customers c ON wp.customer_id = c.customer_id
)
SELECT sale_year FROM with_customers
