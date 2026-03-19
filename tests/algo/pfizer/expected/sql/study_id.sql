-- Source: deterministic match from star_schema_pipeline
WITH
with_sites AS (
  SELECT t.trial_id AS study_id
  FROM trials t
  LEFT JOIN research_sites rs ON t.site_code = rs.site_code
)
SELECT study_id FROM with_sites
