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
    SUM(CASE WHEN txn_type = 'credit' THEN amount ELSE 0 END) AS total_credits,
    SUM(CASE WHEN txn_type = 'debit' THEN amount ELSE 0 END) AS total_debits
  FROM joined
  GROUP BY account_id, holder_name
),
with_rating AS (
  SELECT
    CASE
      WHEN total_credits - total_debits >= 10000 THEN 'Platinum'
      WHEN total_credits - total_debits >= 5000 THEN 'Gold'
      WHEN total_credits - total_debits >= 0 THEN 'Silver'
      ELSE 'Bronze'
    END AS activity_rating
  FROM aggregated
)
SELECT activity_rating FROM with_rating
