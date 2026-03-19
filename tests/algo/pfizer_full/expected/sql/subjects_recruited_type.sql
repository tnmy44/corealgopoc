-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    TRIM(SUBJECT_TYPE) AS SUBJECTS_RECRUITED_TYPE
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT SUBJECTS_RECRUITED_TYPE FROM metrics_joined
