SELECT
  t.amount
FROM transactions t
JOIN persons p ON t.person_id = p.person_id
