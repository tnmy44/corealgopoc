-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    TRIM(DATA_COLLECTION_SECONDARY) AS SECONDARY_DATA_COLLECTION
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT SECONDARY_DATA_COLLECTION FROM metrics_joined
