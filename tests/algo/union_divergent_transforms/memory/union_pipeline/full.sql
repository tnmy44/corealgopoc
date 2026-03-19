SELECT
  p.receipt_no AS txn_id,
  CAST(strptime(p.sale_date, '%m/%d/%Y') AS DATE) AS txn_date,
  p.total_cents / 100.0 AS amount,
  p.customer_email
FROM pos_sales p
UNION ALL
SELECT
  o.order_id AS txn_id,
  CAST(o.order_timestamp AS DATE) AS txn_date,
  o.subtotal + o.tax AS amount,
  o.email AS customer_email
FROM online_sales o
