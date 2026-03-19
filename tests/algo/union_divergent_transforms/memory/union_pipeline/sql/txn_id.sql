SELECT
  p.receipt_no AS txn_id
FROM pos_sales p
UNION ALL
SELECT
  o.order_id AS txn_id
FROM online_sales o
