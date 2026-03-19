SELECT
  SUM(le.entry_amount) / 100.0 AS loan_amount_usd
FROM ledger_entries le
INNER JOIN accounts a ON le.account_id = a.account_id
WHERE le.entry_type = 'debit'
GROUP BY a.account_id
