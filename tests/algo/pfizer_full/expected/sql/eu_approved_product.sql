-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    CASE
      WHEN APPROVED_PRODUCT_EU = TRUE THEN 'Y'
      WHEN APPROVED_PRODUCT_EU = FALSE THEN 'N'
      ELSE NULL
    END AS EU_APPROVED_PRODUCT
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT EU_APPROVED_PRODUCT FROM metrics_joined
