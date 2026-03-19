-- Source: LLM fallback
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
)
SELECT loan_id FROM active_only
