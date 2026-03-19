-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    CAST(SAP_COMPLETION_PCT AS BIGINT) AS SAP_PCT_COMPLETED
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT SAP_PCT_COMPLETED FROM metrics_joined
