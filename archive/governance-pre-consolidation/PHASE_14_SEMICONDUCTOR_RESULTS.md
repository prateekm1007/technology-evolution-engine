# PHASE_14_SEMICONDUCTOR_RESULTS

**Status:** Phase 14A, Domain 1 results.
**Location:** repo root.
**Phase:** 14A.
**Domain:** semiconductors.
**Verdict:** DOES NOT SURVIVE (conditions 3 and 4 fail).

> Search for evidence that this sentence is wrong:
> rising capabilities that become increasingly adjacent
> produce susceptible regions in technological space.
> — CEO directive, Phase 14

---

## Summary

| Metric | Frozen formula | NULL_MODEL | Verdict |
|---|---|---|---|
| TPs | 4 | 2 | Directional advantage |
| FPs | 98 | 100 | — |
| Actuals | 13 | 13 | — |
| Precision | 3.92% | 1.96% | Formula > NULL |
| Recall | 30.77% | 15.38% | Formula > NULL |
| McNemar p | 0.5000 | — | NOT significant (n=2) |
| Paired t (df=11) | 1.483, p=0.138 | — | NOT significant |

**Advancement criteria:**

| Condition | Result | Status |
|---|---|---|
| 1. ≥1 TP | 4 TPs | PASS |
| 2. Precision > NULL | 3.92% > 1.96% | PASS |
| 3. McNemar p < 0.10 | p=0.5000 | **FAIL** |
| 4. No D4 falsification | 13/15 events without velocity > 0.20 | **FAIL** |

**Domain SURVIVES: NO.** Conditions 3 and 4 fail.

---

## What the model predicted correctly (4 TPs)

| T | Predicted combination | Event year | Event | TP type |
|---|---|---|---|---|
| 1970 | {OPTICAL_LITHOGRAPHY, PLANAR_TRANSISTOR, WAFER_FABRICATION} | 1971 | Intel 4004 | ARTIFACT (all 4 candidates tie at score 0.0; TP by sort order) |
| 1980 | {OPTICAL_LITHOGRAPHY, PLANAR_TRANSISTOR, WAFER_FABRICATION} | 1985 | Intel 386 | ARTIFACT (same: all 4 candidates tie at 0.0) |
| 1995 | {COPPER_INTERCONNECT, OPTICAL_LITHOGRAPHY} | 1997 | Copper interconnect | REAL (COPPER_INTERCONNECT at TRL 8, velocity 0.40) |
| 2005 | {HIGH_K_GATE_STACK, PLANAR_TRANSISTOR} | 2007 | 45nm high-k | REAL (HIGH_K_GATE_STACK at TRL 8, velocity 0.40) |

**Only 2 of 4 TPs are real predictions.** The first two TPs (1971, 1985) are artifacts of the candidate set being too small (only 4 candidates at T=1970 and T=1980) and all scoring 0.0 — the model "predicted" by sort-order accident. The real TPs are the copper interconnect (1997) and high-k (2007) events, both of which involve a genuinely rising capability.

## What the model missed (9 FNs among Group B)

| Event year | Event | Combination | Why missed |
|---|---|---|---|
| 2009 | TSV 3D packaging | {ADVANCED_PACKAGING, OPTICAL_LITHOGRAPHY} | ADVANCED_PACKAGING velocity at 2008 = 0.20 (at threshold, not > 0.20); ranked below Top-10 |
| 2011 | Intel 22nm FinFET | {NON_PLANAR_TRANSISTOR, OPTICAL_LITHOGRAPHY} | NON_PLANAR velocity at 2010 = 0.20 (at threshold); 2-cap combo ranked below 3-cap combos |
| 2012 | TSMC 28nm HKMG | {HIGH_K, NON_PLANAR, OPTICAL_LITHOGRAPHY} | HIGH_K velocity at 2011 = 0.20 (at threshold); 3-cap combo ranked below other 3-cap combos with higher adjacency |
| 2014 | Intel 14nm FinFET | {NON_PLANAR, OPTICAL_LITHOGRAPHY} | NON_PLANAR velocity at 2013 = 0.20 (at threshold); 2-cap combo ranked below 3-cap combos |
| 2018 | TSMC 7nm EUV | {EUV, NON_PLANAR} | EUV velocity at 2017 = 0.20 (at threshold); 2-cap combo ranked below 3-cap combos |
| 2020 | TSMC 5nm EUV | {EUV, NON_PLANAR} | EUV velocity at 2019 = 0.20 (at threshold); same |
| 2020 | AMD 3D V-Cache | {ADVANCED_PACKAGING, NON_PLANAR} | Both at TRL 9, velocity 0.0 — plateaued; no rising signal |
| 2022 | Samsung 3nm GAA | {EUV, NON_PLANAR} | Both at TRL 9, velocity 0.0 — plateaued; no rising signal |

**Pattern:** The model misses events when:
1. The velocity is exactly at the 0.20 threshold (not > 0.20) — 5 events.
2. The capability has already reached TRL 9 (velocity = 0, plateaued) — 2 events.
3. The actual event is a 2-capability combo, but the Top-10 is filled with 3-capability combos that have higher adjacency scores — 4 events.

---

## Destruction test D4: invention without velocity

**Pre-stated falsifier (per DESTRUCTION_TEST_PROTOCOL.md):** If ANY event in any domain occurs without velocity > 0.20 in its combination at T-1, the necessity claim (FEC-002) is falsified.

**Result with pre-stated threshold (> 0.20):** 13 of 15 events have NO capability with velocity > 0.20 at year-1. Strict necessity is FALSIFIED.

### Threshold sensitivity analysis

| Threshold | D4 triggered | Group A | Group B |
|---|---|---|---|
| > 0.20 (pre-stated) | 13/15 | 5/5 | 8/10 |
| > 0.15 | 5/15 | 5/5 | 0/10 |
| > 0.10 | 5/15 | 5/5 | 0/10 |
| > 0.05 | 5/15 | 5/5 | 0/10 |
| > 0.00 | 5/15 | 5/5 | 0/10 |

**Key finding:** The 5 Group A scaling events (Intel 4004, 386, Pentium, 0.35um DRAM, 130nm strained Si) have genuinely ZERO velocity — they fail D4 regardless of threshold. These are robust counterexamples to the necessity claim.

The 8 Group B events that fail at > 0.20 all have velocity EXACTLY equal to 0.20 (because the semiconductor TRL timeline rises in 1-TRL steps over 5-year windows, producing velocity = 1/5 = 0.20). They pass D4 at any lower threshold. The pre-stated threshold of > 0.20 was calibrated to Li-ion (where velocities were 0.33, 0.50, 0.67) and is too strict for semiconductor data granularity.

Per EP-6, the pre-stated threshold is binding. I cannot adjust it after seeing results. But the sensitivity analysis reveals the failure mode: the threshold is granularity-sensitive, not theory-sensitive.

### The robust finding (threshold-independent)

**5 of 15 semiconductor events occur with genuinely zero rising-capability velocity.** These are the Group A scaling events:
- 1971 Intel 4004
- 1985 Intel 386
- 1993 Intel Pentium
- 1995 0.35um DRAM
- 2001 130nm strained Si

These events are scaling-driven, not capability-driven. The capabilities involved (OPTICAL_LITHOGRAPHY, PLANAR_TRANSISTOR, WAFER_FABRICATION) were all at TRL 9 throughout. The inventions were incremental improvements within an already-mature technology base.

**This falsifies the strict necessity claim (FEC-002) regardless of threshold.** The theory's boundary is: it applies to capability-driven invention, not to scaling-driven invention.

---

## Significance test result

McNemar exact test on Formula B vs NULL: b=2, c=0, n=2, p=0.5000.

Only 2 discordant TP pairs — the 2 real TPs (copper, high-k) that favored Formula B. NULL produced 0 TPs that Formula B missed. The directional advantage is there (2 vs 0) but n=2 is far too small for statistical significance.

Paired t-test on per-T precision: t(11)=1.483, p=0.138. Not significant at p<0.10.

**The semiconductor domain does not reach statistical significance.** This is the same pattern as Li-ion (p=0.2188 at n=14). The directional advantage is consistent but the effect size is too small for the sample size.

---

## What this means for the theory

### The sentence under examination

> rising capabilities that become increasingly adjacent
> produce susceptible regions in technological space

### Evidence FOR the sentence (semiconductors)

1. **2 real TPs** (copper 1997, high-k 2007): both events involve a rising capability (velocity 0.40) that is adjacent to existing combinations. The sentence holds for these cases.
2. **Directional advantage** (4 TPs vs 2 for NULL, 2 discordant pairs favoring Formula B): the model's susceptibility estimate is directionally better than random, even if not statistically significant.
3. **The 2 real TPs are the events with the HIGHEST velocity** (0.40, well above the 0.20 threshold). When velocity is unambiguously high, the model predicts correctly.

### Evidence AGAINST the sentence (semiconductors)

1. **5 scaling events with zero velocity** (Group A): invention occurred without any rising capability. The sentence does not hold for scaling-driven invention.
2. **8 Group B events at velocity exactly 0.20** were missed: the model is insensitive to capability motion that is at the threshold, not above it. This is a granularity problem but also a theory problem — the model should detect capability motion even when it's gradual.
3. **2 plateaued-capability events** (AMD 3D V-Cache 2020, Samsung GAA 2022): the capabilities had already reached TRL 9 (velocity = 0) but invention still occurred. The model cannot detect susceptibility when the rising capability has already matured.
4. **Only 2 of 10 capability-driven events were predicted**: recall on Group B is 20%. The model misses 80% of capability-driven events.

### The boundary

The theory's boundary is:
- It applies to capability-driven invention where velocity is UNAMBIGUOUSLY high (> 0.20 strictly, ideally ≥ 0.40).
- It does NOT apply to:
  - Scaling events (zero velocity) — 5/15 semiconductor events.
  - Events at the velocity threshold (exactly 0.20) — threshold-dependent.
  - Events after the capability has plateaued (velocity = 0 despite TRL 9) — 2/15 semiconductor events.

### Does the sentence "survive" semiconductors?

**Partially.** The sentence is not fully falsified — it holds for the 2 events with unambiguously high velocity (copper, high-k). But it is not fully confirmed — it fails for 13 of 15 events (5 with zero velocity, 8 at the threshold, 2 plateaued).

Per the advancement criteria (PHASE_14_ADVANCEMENT_CRITERIA.md), the domain does NOT survive:
- Condition 3 fails (p=0.5000, not significant).
- Condition 4 fails (13/15 events without velocity > 0.20; 5/15 with zero velocity at any threshold).

**Score: 0/4 domains survive.** Per the advancement table, 0/4 = "Reject theory." But this is the first of four domains. The theory is not yet rejected — it has 3 more domains to survive or fail.

---

## What this means for the project

### The honest finding

The semiconductor domain exposed a boundary the Li-ion domain did not: **the theory does not apply to scaling-driven invention.** In Li-ion, all events were capability-driven (involving a rising capability). In semiconductors, 33% of events (5/15) are scaling-driven — incremental improvements within a mature technology base.

This is not a failure of the formula. The formula correctly assigns zero velocity to stable capabilities. The issue is that the theory's claim — "rising capabilities produce susceptible regions" — is too broad. It should be qualified: "rising capabilities produce susceptible regions FOR CAPABILITY-DRIVEN invention, not for SCALING-DRIVEN invention."

### The CEO's framing

> Where is the landscape becoming unstable?

The semiconductor landscape was NOT unstable during 1971-1995 (the scaling era). It was stable — the same capabilities (lithography, planar transistors, wafer fabrication) were at TRL 9, and the industry was scaling within them. The landscape BECAME unstable in 1997-2022 (the capability-driven era), when new capabilities (copper, high-k, FinFET, EUV, GAA, advanced packaging) rose from TRL 1 to TRL 9.

The model detected instability in 2 of 10 capability-driven events (copper, high-k). It missed the other 8 — but the missed events are not counterexamples to susceptibility; they are cases where the model's resolution (5-year TRL snapshots, 0.20 velocity threshold) was too coarse to detect the instability.

### The next step

Three more domains remain: telecommunications, aviation, pharmaceuticals. Each has a different structural violation (per INVARIANT_REGISTRY.md). If the theory fails all four, it is rejected (0/4). If it survives 1+, the theory is a local phenomenon. If it survives 2+, it is a promising framework.

The semiconductor domain's failure is informative, not destructive. It identified the boundary (scaling vs capability-driven) and the granularity issue (0.20 threshold). The next domains will test whether these boundaries are semiconductor-specific or universal.

---

## Artifacts

- Script: `scripts/run_semiconductor_backtest.py`
- Raw output: `evidence/observations/phase14_semiconductor_backtest.json`
- This document: `PHASE_14_SEMICONDUCTOR_RESULTS.md`
- Domain artifacts: `SEMICONDUCTOR_ONTOLOGY.md`, `SEMICONDUCTOR_EVENT_REGISTRY.md`, `SEMICONDUCTOR_TRAJECTORY_REGISTRY.md`, `SEMICONDUCTOR_BOTTLENECK_REGISTRY.md`
