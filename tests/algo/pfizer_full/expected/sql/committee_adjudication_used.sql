-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    TRIM(ADJUDICATION_COMMITTEE) AS COMMITTEE_ADJUDICATION_USED
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT COMMITTEE_ADJUDICATION_USED FROM metrics_joined
