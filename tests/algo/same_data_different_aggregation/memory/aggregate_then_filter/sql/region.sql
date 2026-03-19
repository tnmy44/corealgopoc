WITH with_customers AS (
  SELECT
    o.store_id,
    o.amount,
    c.name AS customer_name
  FROM orders o
  JOIN customers c ON o.customer_id = c.customer_id
),
with_stores AS (
  SELECT
    wc.customer_name,
    wc.amount,
    s.region
  FROM with_customers wc
  JOIN stores s ON wc.store_id = s.store_id
),
aggregated AS (
  SELECT
    customer_name,
    region,
    SUM(amount) AS total_spent
  FROM with_stores
  GROUP BY customer_name, region
),
filtered AS (
  SELECT
    region
  FROM aggregated
  WHERE total_spent >= 150
)
SELECT
  region
FROM filtered
