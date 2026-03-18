# String Matching Algorithm Evaluation

## Algorithms


| Algorithm   | Description                                                                                 |
| ----------- | ------------------------------------------------------------------------------------------- |
| Exact       | 1.0 if normalised strings are equal, else 0.0                                               |
| Levenshtein | 1 - (edit distance / max length) on normalised strings                                      |
| JaroWinkler | Jaro-Winkler similarity with prefix boost, good for short identifiers                       |
| TokenSet    | Jaccard overlap on word-token sets — handles word reordering                                |
| Subsequence | Longest common subsequence length / max length                                              |
| Semantic    | Cosine similarity on `all-MiniLM-L6-v2` sentence-transformer embeddings — captures synonyms |
| X+Y         | Weighted 50/50 average of two algorithms                                                    |


## Results

Evaluated on 234 cross-dataset synonym pairs from GSMBS and MFA column names. Cost model: FP (wrong match) = 5, FN (missed match, LLM fallback) = 1.


| Algorithm            | OptCost | Thresh | FP%   | Margin | Hit@1 | Hit@3 | MRR   | Avg Time |
| -------------------- | ------- | ------ | ----- | ------ | ----- | ----- | ----- | -------- |
| Semantic             | 0.778   | 0.705  | 38.0% | +0.065 | 62.0% | 79.1% | 0.717 | 60 us    |
| Levenshtein+TokenSet | 0.833   | 0.643  | 39.3% | +0.070 | 60.7% | 79.9% | 0.715 | 3 us     |
| Semantic+TokenSet    | 0.838   | 0.658  | 35.9% | +0.092 | 64.1% | 82.9% | 0.740 | 3 us     |
| TokenSet             | 0.868   | 0.500  | 43.2% | +0.100 | 56.8% | 75.6% | 0.681 | 2 us     |
| JaroWinkler+TokenSet | 0.872   | 0.693  | 38.5% | +0.055 | 61.5% | 80.3% | 0.722 | 3 us     |
| Semantic+Levenshtein | 0.906   | 0.738  | 38.0% | +0.067 | 62.0% | 82.5% | 0.729 | 2 us     |
| JaroWinkler          | 0.949   | 0.954  | 57.7% | -0.039 | 42.3% | 57.3% | 0.529 | 1 us     |
| Levenshtein          | 0.953   | 0.786  | 49.1% | +0.009 | 50.9% | 69.2% | 0.616 | 1 us     |
| Exact                | 0.987   | 0.000  | 95.7% | +0.026 | 4.3%  | 5.6%  | 0.078 | 1 us     |
| Subsequence          | 0.987   | 0.931  | 50.4% | -0.010 | 49.6% | 65.8% | 0.599 | 1 us     |


## Column definitions

- **OptCost** — Minimum expected cost per query at the optimal score threshold. Lower is better. At threshold, the engine either accepts top match (cost 0 if correct, cost 5 if wrong) or abstains to LLM (cost 1).
- **Thresh** — Score threshold that achieves OptCost.
- **FP%** — Fraction of queries where the top-ranked result is not the true synonym (raw, no threshold).
- **Margin** — Mean(synonym score - best non-synonym score). Positive = clean separation; negative = non-synonyms frequently outscore the synonym.
- **Hit@1 / Hit@3** — Fraction of queries where the true synonym is ranked 1st / within top 3.
- **MRR** — Mean Reciprocal Rank (average of 1/rank).
- **Avg Time** — Average wall-clock time per `score()` call. Combo matchers benefit from embedding cache warmup.

