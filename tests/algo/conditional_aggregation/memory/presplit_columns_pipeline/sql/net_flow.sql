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
)
SELECT total_credits - total_debits AS net_flow
FROM aggregated
