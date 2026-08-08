# Known Measurement Defects

Three defects are frozen as evidence at commit 777cb6d. These have been measured, not repaired.

## DEFECT-001 — Proposal-locus leakage

The production scorer can award discovery credit from entities extracted directly from either input literature even when the system did not propose the bridge.

The scoring code (lines 420-425 of `benchmarks/discovery_capability_benchmark.py`):
```python
if not bridge_found:
    for e in ents_a + ents_b:
        if _bridge_matches(gold["bridge"], e.text):
            bridge_found = True
            break
```

Evidence:
```
2 / 8 current TPs come from ambient fallback
25% of positive discoveries do not require the system to propose the bridge
```

The two affected gold items:
- DISC-GOLD-004 (thermal regulation) — matched "stable thermal conditions" from entities A
- DISC-GOLD-005 (contact angle) — matched "surface wettability angle" from entities A

## DEFECT-002 — FP=0 by construction

The production scorer initializes FP to zero and does not increment it.

The scoring code (lines 386-431 of `benchmarks/discovery_capability_benchmark.py`):
```python
tp = 0  # discovered the bridge + connection
fp = 0  # found a connection but wrong bridge  ← NEVER INCREMENTED
fn = 0  # missed the bridge entirely
```

The loop only does `tp += 1` or `fn += 1`. It never does `fp += 1`.

Therefore:
```
precision = 1.0
```
is structurally guaranteed whenever TP > 0. This is a tautology, not a measurement.

If the 16 incorrect proposals were counted as FP:
```
precision = 6 / (6 + 16) = 0.2727
```

## DEFECT-003 — Loose matcher

The current matcher (`_bridge_matches()`) grants matches through:
1. Exact canonical match
2. Substring match
3. Token overlap (any shared token ≥ 4 characters)

Stage −1 found:
```
20 current matches (across shared + ambient candidates)
0 strict normalized matches (exact canonical only)
20 disagreements (all current matches are token-overlap or substring)
```

The matcher is doing substantial work converting lexical overlap into discovery credit.

Examples of loose matches:
- "thermal regulation" → "stable thermal conditions" (token overlap: "thermal")
- "spin polarization" → "Magnetic resonance imaging detector" (token overlap via "spin")
- "photon energy" → "light quantum energy" (token overlap: "energy")

Do not call this evidence of scientific semantic validity. The matcher is not proving a semantic relationship — it is granting lexical overlap credit.
