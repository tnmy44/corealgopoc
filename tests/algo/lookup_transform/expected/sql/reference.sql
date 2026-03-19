-- Source: deterministic match from simple_pipeline
WITH
with_channels AS (
  SELECT
    s.sale_id,
    cc.channel_code
  FROM sales s
  LEFT JOIN channel_codes cc ON s.sale_id = cc.sale_id
),
transformed AS (
  SELECT
    CASE
      WHEN channel_code = 1 THEN 'WHOLESALE'
      WHEN channel_code = 2 THEN 'RETAIL'
      WHEN channel_code = 3 THEN 'ONLINE'
      ELSE NULL
    END AS reference
  FROM with_channels
)
SELECT reference FROM transformed
