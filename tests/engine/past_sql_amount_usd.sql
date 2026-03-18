WITH raw_pos_transactions_unified_transactions AS (

  SELECT * 
  
  FROM raw_pos_transactions

),

raw_rep_roster_dim_rep_unified_transactions AS (

  SELECT * 
  
  FROM raw_rep_roster

),

pos_with_rep AS (

  SELECT 
    p.total_sale,
    p.exchange_rate_to_usd,
  
  FROM raw_pos_transactions_unified_transactions AS p
  LEFT JOIN raw_rep_roster_dim_rep_unified_transactions AS r
     ON p.salesperson_code = r.salesperson_code

),

pos_amount_converted AS (

  SELECT 
    total_sale * exchange_rate_to_usd AS amount_usd
  
  FROM pos_with_rep

),

pos_standardized AS (

  SELECT 
    amount_usd
  
  FROM pos_amount_converted

),

pos_transaction_data AS (

  SELECT 
    amount_usd,
  
  FROM pos_standardized

),

raw_crm_opportunities_dim_product_unified_transactions AS (

  SELECT * 
  
  FROM raw_crm_opportunities

),

crm_with_rep AS (

  SELECT 
    c.amount,
  
  FROM raw_crm_opportunities_dim_product_unified_transactions AS c
  LEFT JOIN raw_rep_roster_dim_rep_unified_transactions AS r
     ON c.owner_id = r.owner_id

),

crm_standardized AS (

  SELECT 
    amount AS amount_usd,
  
  FROM crm_with_rep

),

crm_transactions AS (

  SELECT 
    amount_usd,
  
  FROM crm_standardized

),

raw_erp_revenue_unified_transactions AS (

  SELECT * 
  
  FROM raw_erp_revenue

),

erp_with_rep AS (

  SELECT 
    e.net_revenue_usd,
  
  FROM raw_erp_revenue_unified_transactions AS e
  LEFT JOIN raw_rep_roster_dim_rep_unified_transactions AS r
     ON e.employee_number = r.employee_number

),

erp_standardized AS (

  SELECT 
    net_revenue_usd AS amount_usd,
  
  FROM erp_with_rep

),

erp_transactions AS (

  SELECT 
    amount_usd,
  
  FROM erp_standardized

),

combined_cte_results AS (

  SELECT * 
  
  FROM crm_transactions
  
  UNION ALL
  
  SELECT * 
  
  FROM erp_transactions

),

all_transactions AS (

  SELECT * 
  
  FROM combined_cte_results
  
  UNION ALL
  
  SELECT * 
  
  FROM pos_transaction_data

),

final AS (

  SELECT 
    amount_usd,
  
  FROM all_transactions

)

SELECT *

FROM final
