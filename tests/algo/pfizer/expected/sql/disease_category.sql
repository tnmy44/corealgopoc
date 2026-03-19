-- Source: deterministic match from star_schema_pipeline
WITH
with_sites AS (
  SELECT t.disease_area AS disease_category
  FROM trials t
  LEFT JOIN research_sites rs ON t.site_code = rs.site_code
)
SELECT disease_category FROM with_sites
