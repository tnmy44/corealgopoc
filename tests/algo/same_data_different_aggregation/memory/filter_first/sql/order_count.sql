WITH filtered_orders AS (
  SELECT
    customer_id,
    store_id
  FROM orders
  WHERE amount >= 75
),
with_stores AS (
  SELECT
    fo.customer_id,
    s.region
  FROM filtered_orders fo
  JOIN stores s ON fo.store_id = s.store_id
),
with_customers AS (
  SELECT
    ws.region,
    c.name AS customer_name
  FROM with_stores ws
  JOIN customers c ON ws.customer_id = c.customer_id
),
aggregated AS (
  SELECT
    COUNT(*) AS order_count
  FROM with_customers
  GROUP BY customer_name, region
)
SELECT
  order_count
FROM aggregated
