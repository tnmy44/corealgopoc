WITH
aggregated AS (
  SELECT product_id, warehouse_id,
         SUM(CASE WHEN movement_type = 'receipt' THEN quantity_change ELSE 0 END) AS total_received,
         SUM(CASE WHEN movement_type = 'shipment' THEN quantity_change ELSE 0 END) AS total_shipped
  FROM inventory_movements
  GROUP BY product_id, warehouse_id
),
with_stock AS (
  SELECT a.product_id, a.warehouse_id,
         a.total_received - a.total_shipped AS current_stock
  FROM aggregated a
),
with_products AS (
  SELECT ws.current_stock * p.unit_cost AS stock_value
  FROM with_stock ws
  LEFT JOIN products p ON ws.product_id = p.product_id
)
SELECT stock_value FROM with_products
