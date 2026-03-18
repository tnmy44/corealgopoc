# Data Profile Matching — Format Discrimination Evaluation

## Algorithms

**Simple** — Averages three ratios: null-rate similarity, unique-rate similarity, and one type-specific signal (mean distance for numeric, avg-length distance for string, true-rate distance for boolean). Cheapest but almost no discrimination power.

**Distribution** — Weighted combination of null-rate, unique-rate, plus richer type-specific signals:
- Numeric: range overlap (w=2), histogram intersection (w=3), mean similarity (w=1)
- String: value cosine similarity (w=3), pattern Jaccard (w=2), length similarity (w=1)
- Boolean: true-rate similarity (w=2)

Best discriminator in the eval (90% disc rate).

**Wasserstein** — Same structure as Distribution but replaces histogram intersection + range overlap with a single Wasserstein (earth-mover) distance normalized by combined range (w=4). For strings, uses pattern *cosine* instead of Jaccard. Scores tend to be higher overall (avg 0.72 positive) but with less separation from negatives.

**Enhanced** — Kitchen-sink approach combining signals from both Distribution and Wasserstein:
- Numeric: histogram intersection (w=3) + Wasserstein (w=3) + std comparison (w=2) + quartile comparison (w=2)
- String: value cosine (w=4) + pattern cosine (w=2) + length (w=1)
- Also uses log-scale cardinality comparison (w=2) instead of linear unique-rate

Despite more signals, slightly worse discrimination (86%) than Distribution alone — the extra features add noise.

**Dist+Wasserstein** — Simple 50/50 weighted average of Distribution and Wasserstein scores. No new logic, just ensembles the two. Tied at 86% discrimination.

## Results

Evaluation tests whether each matcher can distinguish same-format pairs (GSMBS vs MFA original) from different-format pairs (GSMBS vs MFA transformed). 50 testable columns out of 145 total.

| Algorithm | Disc% | Avg Pos | Avg Neg | Margin | Opt Acc | Threshold | Avg Time |
|---|---|---|---|---|---|---|---|
| Distribution | 90.0% | 0.597 | 0.361 | +0.236 | 82.0% | 0.416 | 151 us |
| Enhanced | 86.0% | 0.601 | 0.405 | +0.195 | 73.0% | 0.513 | 169 us |
| Dist+Wasserstein | 86.0% | 0.659 | 0.470 | +0.189 | 75.0% | 0.656 | 171 us |
| Wasserstein | 84.0% | 0.721 | 0.578 | +0.142 | 66.0% | 0.486 | 29 us |
| Simple | 66.0% | 0.817 | 0.790 | +0.028 | 57.0% | 0.860 | 1 us |

**Metrics:**
- **Disc%** — % of columns where positive score > negative score
- **Avg Pos / Avg Neg** — mean score for same-format / different-format pairs
- **Margin** — mean(positive - negative), higher is better
- **Opt Acc** — best accuracy over all thresholds classifying positive+negative pairs
- **Threshold** — optimal accept/reject threshold for that accuracy
