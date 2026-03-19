-- Source: expression from high_overlap_single_source, join from medium_overlap_split_tables
SELECT
  CASE
    WHEN o.region_code IN ('NY', 'NJ', 'CT') THEN 'Northeast'
    WHEN o.region_code IN ('CA', 'OR', 'WA') THEN 'West'
    ELSE 'Other'
  END AS region
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
