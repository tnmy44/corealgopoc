WITH normalized_pos AS (
  SELECT
    p.txn_id
  FROM pos_txns p
),
normalized_online AS (
  SELECT
    o.txn_id
  FROM online_txns o
),
all_txn AS (
  SELECT * FROM normalized_pos
  UNION ALL
  SELECT * FROM normalized_online
)
SELECT
  txn_id
FROM all_txn
