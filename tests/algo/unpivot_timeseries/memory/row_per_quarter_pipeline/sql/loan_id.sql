WITH
active_loans AS (
  SELECT *
  FROM loan_snapshots
  WHERE balance > 0
)
SELECT loan_id
FROM active_loans
