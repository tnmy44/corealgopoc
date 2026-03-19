-- Source: deterministic match from star_schema_pipeline
WITH
with_sites AS (
  SELECT t.enrolled_patients AS enrollment_count
  FROM trials t
  LEFT JOIN research_sites rs ON t.site_code = rs.site_code
)
SELECT enrollment_count FROM with_sites
