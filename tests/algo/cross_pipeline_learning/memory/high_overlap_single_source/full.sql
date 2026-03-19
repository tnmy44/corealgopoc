SELECT
  od.order_id AS loan_id,
  CONCAT(od.customer_first_name, ' ', od.customer_last_name) AS borrower_name,
  od.amount_cents / 100.0 AS loan_amount_usd,
  CASE
    WHEN od.risk_score >= 80 THEN 'LOW'
    WHEN od.risk_score >= 50 THEN 'MEDIUM'
    ELSE 'HIGH'
  END AS risk_category,
  CASE
    WHEN od.region_code IN ('NY', 'NJ', 'CT') THEN 'Northeast'
    WHEN od.region_code IN ('CA', 'OR', 'WA') THEN 'West'
    ELSE 'Other'
  END AS region
FROM order_details od
