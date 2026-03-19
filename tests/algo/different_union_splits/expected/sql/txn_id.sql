WITH normalized_india AS (
  SELECT
    i.txn_id
  FROM india_txns i
),
normalized_us AS (
  SELECT
    u.txn_id
  FROM us_txns u
),
all_txn AS (
  SELECT * FROM normalized_india
  UNION ALL
  SELECT * FROM normalized_us
)
SELECT
  txn_id
FROM all_txn
