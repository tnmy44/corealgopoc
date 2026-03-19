-- Source: expression from high_overlap_single_source, join from medium_overlap_split_tables
SELECT
  o.order_id AS loan_id
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
