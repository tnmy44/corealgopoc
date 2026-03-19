WITH
with_customers AS (
  SELECT s.sale_id, s.quantity, s.unit_price, s.sale_date, s.product_id,
         c.customer_name, c.region
  FROM sales s
  LEFT JOIN customers c ON s.customer_id = c.customer_id
),
with_products AS (
  SELECT wc.sale_id, wc.quantity, wc.unit_price, wc.sale_date,
         wc.customer_name, wc.region,
         p.category AS product_category
  FROM with_customers wc
  LEFT JOIN products p ON wc.product_id = p.product_id
),
transformed AS (
  SELECT sale_id, customer_name, product_category,
         quantity * unit_price AS total_price,
         EXTRACT(YEAR FROM CAST(sale_date AS DATE)) AS sale_year,
         region
  FROM with_products
)
SELECT * FROM transformed
