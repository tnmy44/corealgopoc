WITH
sales_computed AS (
  SELECT sale_id, product_id, customer_id,
         quantity * unit_price AS total_price,
         EXTRACT(YEAR FROM CAST(sale_date AS DATE)) AS sale_year
  FROM sales
),
with_products AS (
  SELECT sc.sale_id, sc.customer_id, sc.total_price, sc.sale_year,
         p.category AS product_category
  FROM sales_computed sc
  LEFT JOIN products p ON sc.product_id = p.product_id
),
with_customers AS (
  SELECT wp.sale_id, c.customer_name, wp.product_category,
         wp.total_price, wp.sale_year, c.region
  FROM with_products wp
  LEFT JOIN customers c ON wp.customer_id = c.customer_id
)
SELECT * FROM with_customers
