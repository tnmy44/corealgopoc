WITH
with_drugs AS (
  SELECT cs.study_id, cs.site_id, cs.investigator_id, cs.indication_id,
         cs.enrollment_count, cs.phase, cs.status,
         d.drug_name, d.therapeutic_area
  FROM clinical_studies cs
  LEFT JOIN drugs d ON cs.drug_id = d.drug_id
),
with_sites AS (
  SELECT wd.study_id, wd.investigator_id, wd.indication_id,
         wd.enrollment_count, wd.phase, wd.status,
         wd.drug_name, wd.therapeutic_area,
         s.site_name, s.country
  FROM with_drugs wd
  LEFT JOIN sites s ON wd.site_id = s.site_id
),
with_investigators AS (
  SELECT ws.study_id, ws.indication_id,
         ws.enrollment_count, ws.phase, ws.status,
         ws.drug_name, ws.therapeutic_area,
         ws.site_name, ws.country,
         i.investigator_name
  FROM with_sites ws
  LEFT JOIN investigators i ON ws.investigator_id = i.investigator_id
),
with_indications AS (
  SELECT wi.study_id, wi.drug_name, wi.therapeutic_area,
         wi.site_name, wi.country, wi.investigator_name,
         ind.indication_name, ind.disease_category,
         wi.enrollment_count, wi.phase, wi.status
  FROM with_investigators wi
  LEFT JOIN indications ind ON wi.indication_id = ind.indication_id
)
SELECT * FROM with_indications
