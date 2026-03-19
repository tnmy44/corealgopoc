SELECT
  t.amount
FROM transactions t
LEFT OUTER JOIN persons p ON t.personid = p.personid
