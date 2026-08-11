# V1.11 VALIDATION SEAL

**Date:** 2026-08-11
**Benchmark:** 50 historical discoveries, blind (pre-discovery evidence only)
**Scorer:** V2 calibrated (EXACT_MATCH / MECHANISM_MATCH / COMPONENT_MATCH / PARTIAL_INSIGHT / FAILURE)

---

## Results

| Metric | Value |
|---|---|
| Total cases | 50 |
| EXACT_MATCH | 1 (2%) |
| MECHANISM_MATCH | 47 (94%) |
| COMPONENT_MATCH | 2 (4%) |
| PARTIAL_INSIGHT | 0 (0%) |
| FAILURE | 0 (0%) |
| **Strict recovery** | **48/50 (96%)** |
| **Any recovery** | **50/50 (100%)** |
| **Average quality** | **0.83** |

## Domain Breakdown

| Domain | Strict Recovery | Rate |
|---|---|---|
| biology | 13/13 | 100% |
| chemistry | 7/7 | 100% |
| computing | 6/6 | 100% |
| engineering | 5/5 | 100% |
| medicine | 10/10 | 100% |
| physics | 2/2 | 100% |
| energy | 5/7 | 71% |

## Pattern Breakdown

| Pattern | Strict Recovery | Rate |
|---|---|---|
| combination | 14/14 | 100% |
| constraint_inversion | 5/5 | 100% |
| contradiction | 1/1 | 100% |
| mechanism_transfer | 10/10 | 100% |
| new_capability | 2/2 | 100% |
| new_synthesis | 1/1 | 100% |
| rare_observation | 1/1 | 100% |
| unexpected_observation | 2/2 | 100% |
| constraint_release | 7/8 | 88% |
| unexpected_property | 5/6 | 83% |

## Known Limitations

1. **LLM-based scorer** — not human expert review; may over-count matches
2. **LLM-based generation** — the same LLM generates proposals and scores them (potential bias)
3. **Pre-discovery evidence is summarized** — not raw papers; information loss possible
4. **No temporal cutoff enforcement on LLM knowledge** — the LLM may know about the discovery from training data
5. **No hard negative comparison** — need to verify nulls score lower
6. **2 cases scored COMPONENT_MATCH not strict** — these are genuine partial matches

## Hashes

- Benchmark dataset: (see benchmark_results_v1_11.json)
- Scorer version: V2
- Results file: benchmark_results_v1_11.json

## Frozen

This benchmark is frozen. No modification to scorer, dataset, or results until human expert review is complete.
