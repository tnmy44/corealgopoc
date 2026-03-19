SELECT
  CONCAT(od.customer_first_name, ' ', od.customer_last_name) AS borrower_name
FROM order_details od
