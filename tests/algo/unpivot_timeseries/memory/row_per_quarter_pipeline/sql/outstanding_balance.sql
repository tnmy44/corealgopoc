WITH
active_loans AS (
  SELECT *
  FROM loan_snapshots
  WHERE balance > 0
)
SELECT balance AS outstanding_balance
FROM active_loans
