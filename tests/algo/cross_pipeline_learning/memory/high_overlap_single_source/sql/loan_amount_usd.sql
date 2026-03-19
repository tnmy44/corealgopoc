SELECT
  od.amount_cents / 100.0 AS loan_amount_usd
FROM order_details od
