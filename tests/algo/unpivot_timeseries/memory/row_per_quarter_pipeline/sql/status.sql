WITH
active_loans AS (
  SELECT *
  FROM loan_snapshots
  WHERE balance > 0
)
SELECT
  CASE
    WHEN delinquency_flag = true AND balance > 10000 THEN 'Critical'
    WHEN delinquency_flag = true THEN 'Watch'
    ELSE 'Current'
  END AS status
FROM active_loans
