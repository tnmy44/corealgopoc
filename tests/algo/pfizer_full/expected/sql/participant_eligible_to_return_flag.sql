-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    TRIM(PARTICIPANT_RETURN_ELIGIBLE) AS PARTICIPANT_ELIGIBLE_TO_RETURN_FLAG
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT PARTICIPANT_ELIGIBLE_TO_RETURN_FLAG FROM metrics_joined
