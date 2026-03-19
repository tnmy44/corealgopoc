-- Source: deterministic match from aggregate_detail
SELECT current_stock * avg_unit_cost AS stock_value FROM inventory_summary
