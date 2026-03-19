SELECT
  CASE
    WHEN a.account_type = 'business' THEN 'LOW'
    ELSE 'HIGH'
  END AS risk_category
FROM ledger_entries le
INNER JOIN accounts a ON le.account_id = a.account_id
WHERE le.entry_type = 'debit'
GROUP BY a.account_id, a.account_type
