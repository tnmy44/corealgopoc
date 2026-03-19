-- Source: deterministic match from left_join_pipeline
-- Current data has unmatched personid (P999), matching left_join_pipeline's profile
SELECT
  t.txnid,
  t.amount,
  p.fullname AS personname
FROM transactions t
LEFT OUTER JOIN persons p ON t.personid = p.personid
