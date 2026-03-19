-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    TRIM(CONTACT_PROVIDER) AS CONTACT_CARD_PROVIDER
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT CONTACT_CARD_PROVIDER FROM metrics_joined
