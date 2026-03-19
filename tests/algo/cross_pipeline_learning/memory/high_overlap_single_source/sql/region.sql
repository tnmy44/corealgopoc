SELECT
  CASE
    WHEN od.region_code IN ('NY', 'NJ', 'CT') THEN 'Northeast'
    WHEN od.region_code IN ('CA', 'OR', 'WA') THEN 'West'
    ELSE 'Other'
  END AS region
FROM order_details od
