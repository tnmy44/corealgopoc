SELECT
  concat('p_', p.person_name) AS person_name
FROM transactions t
JOIN persons p ON t.person_id = p.person_id
