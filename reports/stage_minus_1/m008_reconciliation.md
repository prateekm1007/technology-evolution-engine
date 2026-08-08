# M-008 Reconciliation

## M-008 source
- File: programs/A_metrology/bootstrap_statistics.py
- Function: m008() (inside bootstrap_all_metrics)
- Test: tests/test_bootstrap_statistics.py::test_m008_fp_floor_has_ci_near_1

## M-008 formula
M-008 = FP floor = F1 of RANDOM candidates under m_synonym (which falls back to m_token).
For each bootstrap resample:
1. Generate random candidates from the entity pool (with replacement, seed=42)
2. Score against gold using _score_f1_dr91 (f1 = 2*recall/(1+recall))
3. The mean across resamples is the FP floor

## M-008 current value
- Point estimate: 0.9189 ± 0.0978 [0.6667, 1.0000]
- N=20, B=200, seed=42

## M-008 relationship to Discovery Capability F1
- M-008 measures: "what F1 does a RANDOM candidate set achieve?"
- Discovery Capability F1 measures: "what F1 does the system's actual extraction achieve?"
- These are DISTINCT metrics measuring DIFFERENT things.
- M-008 is the FP floor for the matcher (random input).
- Discovery Capability F1 is the actual system performance.

## Why 0.9189 is NOT an FP floor for Discovery Capability
The value 0.9189 appears in TWO contexts that were incorrectly conflated:
1. OLD discovery_capability_score.json: F1=0.9189 (circular-synonym F1, cycle 201-270)
   → This was the system's actual F1, inflated by circular synonyms.
   → It was NOT an FP floor. It was a (corrupted) measurement of system performance.
2. M-008 in bootstrap_statistics.json: 0.9189 (random candidate FP floor, cycle 261+)
   → This IS an FP floor, but for RANDOM candidates, not for the system.
   → The coincidence that both values are 0.9189 is just that — coincidence.

The conflation happened because:
- The old circular F1 happened to be 0.9189
- The random-candidate FP floor also happens to be ~0.9189
- These are different measurements that happen to produce similar numbers
  because the matcher (m_token) is so lenient that random candidates match at ~92%

## Conclusion
M-008 (FP floor) and Discovery Capability F1 are distinct metrics.
The 0.9189 value in the old discovery_capability_score.json was NOT an FP floor.
The 0.9189 value in M-008 IS an FP floor, but for random candidates, not system performance.
These must never be conflated again.
