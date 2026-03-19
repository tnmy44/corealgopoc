WITH
active_loans AS (
  SELECT *
  FROM loan_snapshots
  WHERE balance > 0
),
with_status AS (
  SELECT
    loan_id,
    borrower AS borrower_name,
    snapshot_quarter AS quarter,
    balance AS outstanding_balance,
    delinquency_flag AS is_delinquent,
    CASE
      WHEN delinquency_flag = true AND balance > 10000 THEN 'Critical'
      WHEN delinquency_flag = true THEN 'Watch'
      ELSE 'Current'
    END AS status
  FROM active_loans
)
SELECT * FROM with_status
