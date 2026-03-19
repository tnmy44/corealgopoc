WITH
with_drugs AS (
  SELECT cs.enrollment_count, cs.site_id, cs.investigator_id, cs.indication_id
  FROM clinical_studies cs
  LEFT JOIN drugs d ON cs.drug_id = d.drug_id
),
with_sites AS (
  SELECT wd.enrollment_count, wd.investigator_id, wd.indication_id
  FROM with_drugs wd
  LEFT JOIN sites s ON wd.site_id = s.site_id
),
with_investigators AS (
  SELECT ws.enrollment_count, ws.indication_id
  FROM with_sites ws
  LEFT JOIN investigators i ON ws.investigator_id = i.investigator_id
),
with_indications AS (
  SELECT wi.enrollment_count
  FROM with_investigators wi
  LEFT JOIN indications ind ON wi.indication_id = ind.indication_id
)
SELECT enrollment_count FROM with_indications
