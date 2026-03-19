WITH
joined AS (
  SELECT
    m.acct_id,
    m.credit_amount,
    m.debit_amount,
    c.client_name
  FROM movements m
  LEFT JOIN clients c ON m.acct_id = c.acct_id
),
aggregated AS (
  SELECT
    acct_id AS account_id,
    client_name AS holder_name,
    SUM(credit_amount) AS total_credits,
    SUM(debit_amount) AS total_debits
  FROM joined
  GROUP BY acct_id, client_name
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
