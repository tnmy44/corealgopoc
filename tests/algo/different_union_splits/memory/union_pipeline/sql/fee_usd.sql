WITH normalized_pos AS (
  SELECT
    p.amount * 0.1 AS fee_usd
  FROM pos_txns p
),
normalized_online AS (
  SELECT
    o.amount * 0.2 AS fee_usd
  FROM online_txns o
),
all_txn AS (
  SELECT * FROM normalized_pos
  UNION ALL
  SELECT * FROM normalized_online
)
SELECT
  fee_usd
FROM all_txn
