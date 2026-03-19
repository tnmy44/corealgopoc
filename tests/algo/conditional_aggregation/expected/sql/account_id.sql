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
    holder_name
  FROM joined
  GROUP BY account_id, holder_name
)
SELECT account_id FROM aggregated
