WITH
with_drugs AS (
  SELECT cs.status, cs.site_id, cs.investigator_id, cs.indication_id
  FROM clinical_studies cs
  LEFT JOIN drugs d ON cs.drug_id = d.drug_id
),
with_sites AS (
  SELECT wd.status, wd.investigator_id, wd.indication_id
  FROM with_drugs wd
  LEFT JOIN sites s ON wd.site_id = s.site_id
),
with_investigators AS (
  SELECT ws.status, ws.indication_id
  FROM with_sites ws
  LEFT JOIN investigators i ON ws.investigator_id = i.investigator_id
),
with_indications AS (
  SELECT wi.status
  FROM with_investigators wi
  LEFT JOIN indications ind ON wi.indication_id = ind.indication_id
)
SELECT status FROM with_indications
