-- Source: expression from high_overlap_single_source, join from medium_overlap_split_tables
SELECT
  CASE
    WHEN o.risk_score >= 80 THEN 'LOW'
    WHEN o.risk_score >= 50 THEN 'MEDIUM'
    ELSE 'HIGH'
  END AS risk_category
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
