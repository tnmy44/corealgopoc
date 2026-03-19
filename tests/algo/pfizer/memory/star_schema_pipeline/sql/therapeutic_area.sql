WITH
with_drugs AS (
  SELECT d.therapeutic_area, cs.site_id, cs.investigator_id, cs.indication_id
  FROM clinical_studies cs
  LEFT JOIN drugs d ON cs.drug_id = d.drug_id
),
with_sites AS (
  SELECT wd.therapeutic_area, wd.investigator_id, wd.indication_id
  FROM with_drugs wd
  LEFT JOIN sites s ON wd.site_id = s.site_id
),
with_investigators AS (
  SELECT ws.therapeutic_area, ws.indication_id
  FROM with_sites ws
  LEFT JOIN investigators i ON ws.investigator_id = i.investigator_id
),
with_indications AS (
  SELECT wi.therapeutic_area
  FROM with_investigators wi
  LEFT JOIN indications ind ON wi.indication_id = ind.indication_id
)
SELECT therapeutic_area FROM with_indications
