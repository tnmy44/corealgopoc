SELECT
  t.txnid
FROM transactions t
LEFT OUTER JOIN persons p ON t.personid = p.personid
