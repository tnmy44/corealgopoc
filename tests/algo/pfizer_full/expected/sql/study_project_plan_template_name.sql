-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    TRIM(PROJECT_TEMPLATE) AS STUDY_PROJECT_PLAN_TEMPLATE_NAME
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT STUDY_PROJECT_PLAN_TEMPLATE_NAME FROM metrics_joined
