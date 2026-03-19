SELECT
  p.customer_email
FROM pos_sales p
UNION ALL
SELECT
  o.email AS customer_email
FROM online_sales o
