SELECT
  p.total_cents / 100.0 AS amount
FROM pos_sales p
UNION ALL
SELECT
  o.subtotal + o.tax AS amount
FROM online_sales o
