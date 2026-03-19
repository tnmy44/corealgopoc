-- Source: deterministic match from union_pipeline
-- Structure adapted: split is now by geography; per-source fee rate derived from txn_type column
WITH normalized_india AS (
  SELECT
    i.txn_id,
    CASE WHEN i.txn_type = 'pos' THEN i.amount * 0.1
         WHEN i.txn_type = 'online' THEN i.amount * 0.2
    END AS fee_usd
  FROM india_txns i
),
normalized_us AS (
  SELECT
    u.txn_id,
    CASE WHEN u.txn_type = 'pos' THEN u.amount * 0.1
         WHEN u.txn_type = 'online' THEN u.amount * 0.2
    END AS fee_usd
  FROM us_txns u
),
all_txn AS (
  SELECT * FROM normalized_india
  UNION ALL
  SELECT * FROM normalized_us
)
SELECT
  txn_id,
  fee_usd * 100 AS fee
FROM all_txn
