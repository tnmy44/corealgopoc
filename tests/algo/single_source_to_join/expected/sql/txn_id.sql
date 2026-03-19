SELECT
  t.txn_id
FROM transactions t
JOIN persons p ON t.person_id = p.person_id
