-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    TRIM(DATA_WITHHELD_FLAG) AS PARTICIPANT_DATA_WITHHELD_UNTIL_LSLV_FLAG
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT PARTICIPANT_DATA_WITHHELD_UNTIL_LSLV_FLAG FROM metrics_joined
