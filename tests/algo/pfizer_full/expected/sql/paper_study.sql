-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    CASE
      WHEN PAPER_CRF_USED = TRUE THEN 'Y'
      WHEN PAPER_CRF_USED = FALSE THEN 'N'
      ELSE NULL
    END AS PAPER_STUDY
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT PAPER_STUDY FROM metrics_joined
