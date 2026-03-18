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
    p.txn_id,
    p.salesperson_code,
    p.total_sale,
    p.transaction_date,
    p.item_sku,
    p.local_currency,
    p.exchange_rate_to_usd,
    r.employee_number,
    r.region
  
  FROM raw_pos_transactions_unified_transactions AS p
  LEFT JOIN raw_rep_roster_dim_rep_unified_transactions AS r
     ON p.salesperson_code = r.salesperson_code

),

pos_amount_converted AS (

  SELECT 
    txn_id,
    salesperson_code,
    total_sale,
    transaction_date,
    item_sku,
    local_currency,
    exchange_rate_to_usd,
    employee_number,
    region,
    total_sale * exchange_rate_to_usd AS amount_usd
  
  FROM pos_with_rep

),

pos_standardized AS (

  SELECT 
    CONCAT('pos-', txn_id) AS transaction_id,
    CAST('POS' AS STRING) AS source_system,
    employee_number,
    item_sku AS product_id,
    amount_usd,
    total_sale AS amount_original,
    local_currency AS currency_original,
    transaction_date,
    region,
    CAST(NULL AS STRING) AS account_name,
    CURRENT_TIMESTAMP() AS loaded_at
  
  FROM pos_amount_converted

),

pos_transaction_data AS (

  SELECT 
    transaction_id,
    source_system,
    employee_number,
    product_id,
    amount_usd,
    amount_original,
    currency_original,
    transaction_date,
    region,
    account_name,
    loaded_at
  
  FROM pos_standardized

),

raw_crm_opportunities_dim_product_unified_transactions AS (

  SELECT * 
  
  FROM raw_crm_opportunities

),

crm_with_rep AS (

  SELECT 
    c.opportunity_id,
    c.owner_id,
    c.account_name,
    c.amount,
    c.close_date,
    c.product_name,
    c.region AS crm_region,
    c.currency,
    r.employee_number,
    r.region AS rep_region
  
  FROM raw_crm_opportunities_dim_product_unified_transactions AS c
  LEFT JOIN raw_rep_roster_dim_rep_unified_transactions AS r
     ON c.owner_id = r.owner_id

),

crm_standardized AS (

  SELECT 
    CONCAT('crm-', opportunity_id) AS transaction_id,
    CAST('CRM' AS STRING) AS source_system,
    employee_number,
    product_name AS product_id,
    amount AS amount_usd,
    amount AS amount_original,
    currency AS currency_original,
    close_date AS transaction_date,
    COALESCE(crm_region, rep_region) AS region,
    account_name,
    CURRENT_TIMESTAMP() AS loaded_at
  
  FROM crm_with_rep

),

crm_transactions AS (

  SELECT 
    transaction_id,
    source_system,
    employee_number,
    product_id,
    amount_usd,
    amount_original,
    currency_original,
    transaction_date,
    region,
    account_name,
    loaded_at
  
  FROM crm_standardized

),

raw_erp_revenue_unified_transactions AS (

  SELECT * 
  
  FROM raw_erp_revenue

),

erp_with_rep AS (

  SELECT 
    e.document_number,
    e.employee_number,
    e.net_revenue_usd,
    e.posting_date,
    e.material_number,
    r.region
  
  FROM raw_erp_revenue_unified_transactions AS e
  LEFT JOIN raw_rep_roster_dim_rep_unified_transactions AS r
     ON e.employee_number = r.employee_number

),

erp_standardized AS (

  SELECT 
    CONCAT('erp-', document_number) AS transaction_id,
    CAST('ERP' AS STRING) AS source_system,
    employee_number,
    material_number AS product_id,
    net_revenue_usd AS amount_usd,
    net_revenue_usd AS amount_original,
    CAST('USD' AS STRING) AS currency_original,
    posting_date AS transaction_date,
    region,
    CAST(NULL AS STRING) AS account_name,
    CURRENT_TIMESTAMP() AS loaded_at
  
  FROM erp_with_rep

),

erp_transactions AS (

  SELECT 
    transaction_id,
    source_system,
    employee_number,
    product_id,
    amount_usd,
    amount_original,
    currency_original,
    transaction_date,
    region,
    account_name,
    loaded_at
  
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
    transaction_id,
    lower(source_system) AS source_system,
    employee_number,
    product_id,
    amount_usd,
    amount_original,
    currency_original,
    transaction_date,
    region,
    account_name,
    loaded_at
  
  FROM all_transactions

)

SELECT *

FROM final
