-- Source: LLM fallback (UNPIVOT transformation has no precedent in memory)
WITH
unpivoted AS (
  SELECT loan_id, borrower_name, 'Q1' AS quarter, q1_balance AS outstanding_balance, q1_delinquent AS is_delinquent FROM loan_performance
  UNION ALL
  SELECT loan_id, borrower_name, 'Q2' AS quarter, q2_balance AS outstanding_balance, q2_delinquent AS is_delinquent FROM loan_performance
  UNION ALL
  SELECT loan_id, borrower_name, 'Q3' AS quarter, q3_balance AS outstanding_balance, q3_delinquent AS is_delinquent FROM loan_performance
  UNION ALL
  SELECT loan_id, borrower_name, 'Q4' AS quarter, q4_balance AS outstanding_balance, q4_delinquent AS is_delinquent FROM loan_performance
),
active_only AS (
  SELECT *
  FROM unpivoted
  WHERE outstanding_balance > 0
),
with_status AS (
  SELECT
    loan_id,
    borrower_name,
    quarter,
    outstanding_balance,
    is_delinquent,
    CASE
      WHEN is_delinquent = true AND outstanding_balance > 10000 THEN 'Critical'
      WHEN is_delinquent = true THEN 'Watch'
      ELSE 'Current'
    END AS status
  FROM active_only
)
SELECT * FROM with_status
