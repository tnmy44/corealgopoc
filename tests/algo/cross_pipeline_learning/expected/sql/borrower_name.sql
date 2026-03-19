-- Source: expression from high_overlap_single_source, join from medium_overlap_split_tables
SELECT
  CONCAT(c.first_name, ' ', c.last_name) AS borrower_name
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
