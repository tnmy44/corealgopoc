-- Source: deterministic match from star_schema_pipeline
WITH
with_sites AS (
  SELECT t.therapeutic_area
  FROM trials t
  LEFT JOIN research_sites rs ON t.site_code = rs.site_code
)
SELECT therapeutic_area FROM with_sites
