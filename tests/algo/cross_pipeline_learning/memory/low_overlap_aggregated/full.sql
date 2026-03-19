SELECT
  a.account_id AS loan_id,
  a.account_holder AS borrower_name,
  SUM(le.entry_amount) / 100.0 AS loan_amount_usd,
  CASE
    WHEN a.account_type = 'business' THEN 'LOW'
    ELSE 'HIGH'
  END AS risk_category,
  a.branch AS region
FROM ledger_entries le
INNER JOIN accounts a ON le.account_id = a.account_id
WHERE le.entry_type = 'debit'
GROUP BY a.account_id, a.account_holder, a.account_type, a.branch
