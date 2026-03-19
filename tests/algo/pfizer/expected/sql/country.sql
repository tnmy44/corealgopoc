-- Source: deterministic match from star_schema_pipeline
WITH
with_sites AS (
  SELECT rs.country
  FROM trials t
  LEFT JOIN research_sites rs ON t.site_code = rs.site_code
)
SELECT country FROM with_sites
