SELECT
  CASE
    WHEN od.risk_score >= 80 THEN 'LOW'
    WHEN od.risk_score >= 50 THEN 'MEDIUM'
    ELSE 'HIGH'
  END AS risk_category
FROM order_details od
