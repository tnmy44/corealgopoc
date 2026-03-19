-- Source: deterministic match from flat_pipeline
-- Adaptation introduces JOIN: past had person_name inline, current splits it into a persons table
SELECT
  t.txn_id,
  t.amount,
  concat('p_', p.person_name) AS person_name
FROM transactions t
JOIN persons p ON t.person_id = p.person_id
