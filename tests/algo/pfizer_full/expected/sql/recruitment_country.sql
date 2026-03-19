-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    TRIM(RECRUITMENT_COUNTRY_LIST) AS RECRUITMENT_COUNTRY
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT RECRUITMENT_COUNTRY FROM metrics_joined
