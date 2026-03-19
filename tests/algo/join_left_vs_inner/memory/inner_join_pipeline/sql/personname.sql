SELECT
  p.fullname AS personname
FROM transactions t
INNER JOIN persons p ON t.personid = p.personid
