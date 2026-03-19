-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    CAST(RECRUITMENT_BEGIN_DATE AS DATE) AS RECRUITMENT_START_DATE
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT RECRUITMENT_START_DATE FROM metrics_joined
