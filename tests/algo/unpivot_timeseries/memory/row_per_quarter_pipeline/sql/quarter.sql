WITH
active_loans AS (
  SELECT *
  FROM loan_snapshots
  WHERE balance > 0
)
SELECT snapshot_quarter AS quarter
FROM active_loans
