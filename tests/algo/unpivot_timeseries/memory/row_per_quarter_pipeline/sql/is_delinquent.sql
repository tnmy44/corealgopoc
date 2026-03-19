WITH
active_loans AS (
  SELECT *
  FROM loan_snapshots
  WHERE balance > 0
)
SELECT delinquency_flag AS is_delinquent
FROM active_loans
