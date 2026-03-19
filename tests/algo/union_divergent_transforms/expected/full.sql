-- Source: deterministic match from union_pipeline
-- Current source schema is close to past target; minor renames and date cast needed
SELECT
  t.txn_id,
  CAST(t.txn_date AS DATE) AS txn_date,
  t.amount_usd AS amount,
  t.cust_email AS customer_email
FROM transactions t
