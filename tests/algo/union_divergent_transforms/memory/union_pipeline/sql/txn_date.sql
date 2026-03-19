SELECT
  CAST(strptime(p.sale_date, '%m/%d/%Y') AS DATE) AS txn_date
FROM pos_sales p
UNION ALL
SELECT
  CAST(o.order_timestamp AS DATE) AS txn_date
FROM online_sales o
