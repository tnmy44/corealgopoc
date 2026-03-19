-- Source: LLM fallback
WITH
joined AS (
  SELECT
    t.account_id,
    t.amount,
    t.txn_type,
    a.holder_name
  FROM transactions t
  LEFT JOIN accounts a ON t.account_id = a.account_id
),
aggregated AS (
  SELECT
    account_id,
    holder_name,
    SUM(CASE WHEN txn_type = 'credit' THEN amount ELSE 0 END) AS total_credits
  FROM joined
  GROUP BY account_id, holder_name
)
SELECT total_credits FROM aggregated
