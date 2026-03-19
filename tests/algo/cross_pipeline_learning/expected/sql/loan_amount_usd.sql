-- Source: expression from high_overlap_single_source, join from medium_overlap_split_tables
SELECT
  o.amount_cents / 100.0 AS loan_amount_usd
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
