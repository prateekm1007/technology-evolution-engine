# AUDIT VERDICT

## Verdict: NOT_TRUSTWORTHY

## 1. Does current scoring require proposal of the bridge?
NO. The scorer falls back to checking ALL extracted entities (lines 420-425
of discovery_capability_benchmark.py). A bridge can receive credit from
ambient entity presence without being proposed by discover_shared_entities().

## 2. Can ambient entity presence produce credit?
YES. 2/8 TPs (25.0%) come from
the ambient fallback, not from shared entity proposals.

## 3. Is FP measured correctly?
NO. FP is initialized to 0 and never incremented. The scoring loop only
does tp+=1 or fn+=1. Precision is always 1.0 by construction — this is
a tautology, not a measurement.

## 4. Is 0.9189 an empirical FP floor?
NO. The 0.9189 in the old discovery_capability_score.json was the
circular-synonym F1. The M-008 value of 0.9189 is a random-candidate
FP floor — a different measurement. The shuffled-gold experiment
(Part 7) is the actual empirical FP floor: mean hit rate = 0.1374.

## 5. What fraction of current TPs depend on fallback?
25.0% (2/8)

## 6. What is the proposal-locus-only result?
- TP=6, FP=0, FN=14
- Precision=1.0000, Recall=0.3000, F1=0.4615

## 7. What is the strict matcher result?
- TP=0, FP=0, FN=20
- Precision=1.0000, Recall=0.0000, F1=0.0000

## 8. What is the shuffled-gold FP floor?
- N=1000 trials, seed=270
- Mean hit rate: 0.1374
- P(shuffled >= current): 0.0020
- Range: [0.0000, 0.4500]

## 9. What is the strict proposal-level precision?
- TP (correct proposals): 0
- FP (incorrect proposals): 16
- Precision: 0.2727
- F1: 0.2857

## 10. Can the current F1 be interpreted as independent invention?
NO. The current F1 of 0.5714 is inflated by:
1. Ambient fallback (2 hits from entity presence, not proposals)
2. FP=0 by construction (precision is a tautology)
3. Token-overlap matching (lenient — gives credit for shared 4+ char tokens)

The honest proposal-only F1 is 0.4615.
The strict proposal+FP F1 is 0.0000.
The empirical FP floor (shuffled gold) is 0.1374.

---

> **H1–H4, Gen 5 discovery claims, and any claim of independent invention
> must not be interpreted as established evidence until the measurement
> defects identified in this audit are repaired and the corrected benchmark
> is independently rerun.**
