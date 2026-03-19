SELECT
  a.account_id AS loan_id
FROM ledger_entries le
INNER JOIN accounts a ON le.account_id = a.account_id
WHERE le.entry_type = 'debit'
GROUP BY a.account_id
