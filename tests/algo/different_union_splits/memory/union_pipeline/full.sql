WITH normalized_pos AS (
  SELECT
    p.txn_id,
    p.amount * 0.1 AS fee_usd
  FROM pos_txns p
),
normalized_online AS (
  SELECT
    o.txn_id,
    o.amount * 0.2 AS fee_usd
  FROM online_txns o
),
all_txn AS (
  SELECT * FROM normalized_pos
  UNION ALL
  SELECT * FROM normalized_online
)
SELECT
  txn_id,
  fee_usd * 100 AS fee
FROM all_txn
