-- Source: expressions from high_overlap_single_source, join from medium_overlap_split_tables
SELECT
  o.order_id AS loan_id,
  CONCAT(c.first_name, ' ', c.last_name) AS borrower_name,
  o.amount_cents / 100.0 AS loan_amount_usd,
  CASE
    WHEN o.risk_score >= 80 THEN 'LOW'
    WHEN o.risk_score >= 50 THEN 'MEDIUM'
    ELSE 'HIGH'
  END AS risk_category,
  CASE
    WHEN o.region_code IN ('NY', 'NJ', 'CT') THEN 'Northeast'
    WHEN o.region_code IN ('CA', 'OR', 'WA') THEN 'West'
    ELSE 'Other'
  END AS region
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
