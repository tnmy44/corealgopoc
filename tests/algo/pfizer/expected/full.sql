-- Source: deterministic match from star_schema_pipeline (adapted: 3 of 4 dimension JOINs removed, only sites JOIN retained)
WITH
with_sites AS (
  SELECT t.trial_id AS study_id,
         t.compound_name AS drug_name,
         t.therapeutic_area,
         rs.facility_name AS site_name,
         rs.country,
         t.principal_investigator AS investigator_name,
         t.indication AS indication_name,
         t.disease_area AS disease_category,
         t.enrolled_patients AS enrollment_count,
         t.trial_phase AS phase,
         t.trial_status AS status
  FROM trials t
  LEFT JOIN research_sites rs ON t.site_code = rs.site_code
)
SELECT * FROM with_sites
