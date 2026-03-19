-- Source: deterministic match from aggregate_detail (adapted: GROUP BY + JOIN removed, pre-aggregated source)
SELECT
  product_name,
  warehouse_id,
  current_stock,
  current_stock * avg_unit_cost AS stock_value
FROM inventory_summary
