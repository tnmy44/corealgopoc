-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    TRIM(RECRUITMENT_DESIGN) AS RECRUITMENT_DESIGN_TYPE
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT RECRUITMENT_DESIGN_TYPE FROM metrics_joined
