WITH
active_loans AS (
  SELECT *
  FROM loan_snapshots
  WHERE balance > 0
)
SELECT borrower AS borrower_name
FROM active_loans
