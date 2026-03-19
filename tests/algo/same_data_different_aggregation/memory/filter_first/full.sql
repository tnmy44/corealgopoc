WITH filtered_orders AS (
  SELECT
    order_id,
    customer_id,
    store_id,
    amount
  FROM orders
  WHERE amount >= 75
),
with_stores AS (
  SELECT
    fo.order_id,
    fo.customer_id,
    fo.amount,
    s.region
  FROM filtered_orders fo
  JOIN stores s ON fo.store_id = s.store_id
),
with_customers AS (
  SELECT
    ws.amount,
    ws.region,
    c.name AS customer_name
  FROM with_stores ws
  JOIN customers c ON ws.customer_id = c.customer_id
),
aggregated AS (
  SELECT
    customer_name,
    region,
    SUM(amount) AS total_spent,
    COUNT(*) AS order_count
  FROM with_customers
  GROUP BY customer_name, region
)
SELECT
  customer_name,
  region,
  total_spent,
  order_count
FROM aggregated
