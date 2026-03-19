WITH
aggregated AS (
  SELECT product_id, warehouse_id
  FROM inventory_movements
  GROUP BY product_id, warehouse_id
),
with_stock AS (
  SELECT a.product_id, a.warehouse_id
  FROM aggregated a
),
with_products AS (
  SELECT p.product_name
  FROM with_stock ws
  LEFT JOIN products p ON ws.product_id = p.product_id
)
SELECT product_name FROM with_products
