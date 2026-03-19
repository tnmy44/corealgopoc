SELECT
  t.txn_id,
  t.amount,
  concat('p_', t.person_name) AS person_name
FROM transactions t
