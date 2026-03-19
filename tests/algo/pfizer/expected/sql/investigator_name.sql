-- Source: deterministic match from star_schema_pipeline
WITH
with_sites AS (
  SELECT t.principal_investigator AS investigator_name
  FROM trials t
  LEFT JOIN research_sites rs ON t.site_code = rs.site_code
)
SELECT investigator_name FROM with_sites
