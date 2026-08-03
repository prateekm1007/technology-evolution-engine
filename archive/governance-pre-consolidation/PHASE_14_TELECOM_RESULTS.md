# PHASE_14_TELECOM_RESULTS

**Status:** Phase 14A, Domain 2 results.
**Location:** repo root.
**Phase:** 14A.
**Domain:** telecommunications.
**Verdict:** DOES NOT SURVIVE (all 4 conditions fail).

---

## Summary

| Metric | Frozen formula | NULL_MODEL | Verdict |
|---|---|---|---|
| TPs | 0 | 2 | Formula WORSE than NULL |
| FPs | 100 | 98 | — |
| Actuals | 11 | 11 | — |
| Precision | 0.00% | 2.00% | Formula < NULL |
| Recall | 0.00% | 18.18% | Formula < NULL |
| McNemar p | 0.5000 (n=2, both favored NULL) | — | NOT significant |
| Paired t (df=9) | -1.500, p=0.134 | — | NOT significant |

**Advancement criteria:**

| Condition | Result | Status |
|---|---|---|
| 1. ≥1 TP | 0 TPs | **FAIL** |
| 2. Precision > NULL | 0.00% < 2.00% | **FAIL** |
| 3. McNemar p < 0.10 | p=0.5000 | **FAIL** |
| 4. No D4 falsification | 12/15 events without velocity > 0.20 | **FAIL** |

**Domain SURVIVES: NO.** All 4 conditions fail. This is worse than semiconductors (which passed conditions 1 and 2).

**Cumulative score: 0/4 domains survive (2 of 4 tested).**

---

## What happened: zero true positives

The frozen formula produced ZERO true positives across all 10 T-points. NULL_MODEL produced 2 TPs (at T=1980 and T=2005, by random chance). The formula is WORSE than random.

### Why the formula failed

The pre-stated structural limitation (per TELECOM_TRAJECTORY_REGISTRY.md) was confirmed by the backtest: **4 of 5 rising capabilities have non-monotonic TRL**. They "re-rise" for each new generation, producing negative velocity during the "drop" phases.

The formula's velocity term `max(dTRL/dt) / 2.0, capped at 1.0` does NOT clamp negative values to 0. When a capability drops from TRL 9 to TRL 5 (to track a new sub-capability), the velocity is `(5-9)/5 = -0.8`, which after `/2.0 = -0.4`, and `min(-0.4, 1.0) = -0.4`. The score becomes negative.

Negative scores sort BELOW zero scores. Combinations with negative-velocity capabilities are ranked below combinations with zero-velocity capabilities. This is the OPPOSITE of what the theory intends — the "re-rising" capability should be the most predictive, but the formula penalizes it.

### The 8 Group B events (capability-driven, should have been predicted)

| Event year | Event | Why missed |
|---|---|---|
| 1983 | AMPS 1G | WIRELESS_PROTOCOL velocity at 1982 = (5-3)/5 = 0.4, /2 = 0.2 — exactly at threshold. The combination {WIRELESS_PROTOCOL, RADIO_TRANSMISSION, INFRASTRUCTURE_DEPLOYMENT} scored 0.2 but was not in top 10 (tie-breaking by sort order, 91 candidates). |
| 1991 | GSM 2G | WIRELESS_PROTOCOL at TRL 9 since 1985 (plateaued). Velocity = 0. No rising signal. |
| 2001 | WCDMA 3G | WIRELESS_PROTOCOL still at TRL 9 (plateaued since 1985). Velocity = 0. |
| 2007 | iPhone | SMART_DEVICE_INTEGRATION at TRL 5 in 2006 (re-rising from 9 to 5). Velocity = (5-9)/5 = -0.8. Score is NEGATIVE. |
| 2009 | LTE 4G | WIRELESS_PROTOCOL still at TRL 9. PACKET_SWITCHING at TRL 9. Both plateaued. Velocity = 0. |
| 2016 | NB-IoT | SMART_DEVICE_INTEGRATION at TRL 5 in 2015 (re-rising from 9 to 5). Velocity = -0.8. Score is NEGATIVE. |
| 2019 | 5G NR sub-6 | SPECTRUM_UTILIZATION at TRL 5 in 2018 (re-rising from 9 to 5 for mmWave). Velocity = -0.8. NETWORK_VIRTUALIZATION at TRL 6, velocity = 0.2. The combination has mixed positive and negative velocities; max is 0.2 (at threshold). |
| 2020 | 5G mmWave | SPECTRUM_UTILIZATION at TRL 9 in 2019 (just re-rose). Velocity = (9-5)/5 = 0.8, /2 = 0.4. But the combination also has WIRELESS_PROTOCOL at TRL 9 (velocity 0). Max velocity = 0.4. The combination scored 0.4 × adjacency, but the candidate set is 154 and top 10 is filled with higher-adjacency combos. |

**Pattern:** The formula cannot detect "re-rising" capabilities. Every generation transition after 1G (1983) produces a velocity signal that is either zero (capability plateaued at TRL 9) or negative (capability "dropped" to track the new sub-capability). The model is blind to 2G, 3G, 4G, 5G, and 6G transitions.

### The 7 Group A events (scaling, correctly not predicted)

All 7 Group A events (IS-95, EV-DO, Galaxy S, LTE-A, Gigabit LTE, 5G SA, 5G Advanced) have zero rising-capability velocity. The formula correctly does not predict them — but it also does not predict the Group B events, so the precision is zero all around.

---

## Destruction test D4: invention without velocity

**Pre-stated threshold (> 0.20):** 12 of 15 events have NO rising capability. Strict necessity is FALSIFIED.

### Threshold sensitivity

| Threshold | D4 triggered | Group A | Group B |
|---|---|---|---|
| > 0.20 (pre-stated) | 12/15 | 5/7 | 7/8 |
| > 0.15 | 11/15 | 5/7 | 6/8 |
| > 0.10 | 11/15 | 5/7 | 6/8 |
| > 0.05 | 11/15 | 5/7 | 6/8 |
| > 0.00 | 11/15 | 5/7 | 6/8 |

**Robust finding (threshold-independent):** 11 of 15 telecom events occur with zero or negative rising-capability velocity. This is HIGHER than semiconductors (5/15 robust) because telecom has more "re-rise" cycles.

The 3 events that survive D4 at any threshold:
- 1983 AMPS (WIRELESS_PROTOCOL genuinely rising for 1G, velocity 0.4)
- 2022 5G SA (NETWORK_VIRTUALIZATION rising, velocity 0.4)
- 2023 5G Advanced (SPECTRUM_UTILIZATION re-rising, velocity 0.8)

These 3 events are the only telecom events the theory's necessity claim can explain. The other 12 events falsify strict necessity.

---

## Significance test result

McNemar: b=0, c=2, n=2, p=0.5000. Both discordant pairs favored NULL_MODEL. The formula is directionally WORSE than random.

Paired t-test: t(9)=-1.500, p=0.134. The negative t-statistic indicates the formula's per-T precision is LOWER than NULL's. Not statistically significant, but directionally negative.

**This is the worst possible result.** The formula doesn't just fail to beat NULL — it loses to NULL. The model's "susceptibility estimates" are anti-correlated with actual invention in the telecom domain.

---

## What this means for the theory

### The sentence under examination

> rising capabilities that become increasingly adjacent
> produce susceptible regions in technological space

### Evidence FOR the sentence (telecom)

1. **3 events survive D4 at any threshold:** AMPS (1983), 5G SA (2022), 5G Advanced (2023). These events involve genuinely rising capabilities (WIRELESS_PROTOCOL for 1G, NETWORK_VIRTUALIZATION for 5G SA, SPECTRUM_UTILIZATION re-rise for 5G Advanced).
2. **The 1G rise (1975-1985) is detected:** WIRELESS_PROTOCOL rises from TRL 3 to TRL 9, and the formula assigns high scores to combinations containing it. The AMPS event (1983) is the one case where the theory's prediction aligns with reality (though it was missed due to tie-breaking, not wrong scoring).

### Evidence AGAINST the sentence (telecom)

1. **Zero true positives.** The formula produced 0 TPs across all 10 T-points. NULL produced 2 TPs. The formula is worse than random.
2. **12 of 15 events falsify strict necessity** (D4 triggered at any threshold). The theory's necessity claim (FEC-002) is falsified for telecom.
3. **The "re-rise" problem is fatal.** Telecom capabilities "re-rise" for each new generation (2G, 3G, 4G, 5G). The formula's velocity term produces negative values during "drop" phases, penalizing the exact capabilities that should be most predictive. The model is structurally blind to generation transitions after 1G.
4. **The coordination bottleneck is invisible to the formula.** Telecom's dominant bottleneck (3GPP standards consensus) is a process, not a capability trajectory. The formula has no way to detect "standards are converging, deployment is imminent."

### The boundary (refined after 2 domains)

After semiconductors (failed) and telecom (failed), the theory's boundary is clearer:

**The theory applies to:**
- Capability-driven invention where velocity is unambiguously positive (> 0.20 strictly).
- Domains where capabilities rise ONCE, monotonically, from TRL 1 to TRL 9.

**The theory does NOT apply to:**
1. **Scaling-driven invention** (zero velocity) — semiconductors Group A, telecom Group A.
2. **Generation-transition invention** (re-rising capabilities) — telecom 2G/3G/4G/5G transitions.
3. **Non-monotonic TRL domains** (capabilities that drop to track new sub-capabilities) — telecom SPECTRUM_UTILIZATION, SMART_DEVICE_INTEGRATION.
4. **Coordination-bottlenecked domains** (standards-body consensus as dominant bottleneck) — telecom 3GPP.
5. **Discontinuous step-rise domains** (lithography generations, protocol generations) — semiconductors, telecom.

### Does the sentence "survive" telecom?

**No.** The sentence is falsified for telecom. The formula produced zero TPs, lost to NULL, and 12/15 events falsify strict necessity. The theory's boundary (capability-driven invention with monotonic TRL rise) does not include telecom.

---

## What this means for the project

### Cumulative status

| Domain | Survives? | TPs | Precision | McNemar p | D4 falsified? |
|---|---|---|---|---|---|
| Semiconductors | NO | 4 (2 real) | 3.92% | 0.5000 | Yes (13/15 at >0.20; 5/15 robust) |
| Telecom | NO | 0 | 0.00% | 0.5000 | Yes (12/15 at >0.20; 11/15 robust) |
| Aviation | pending | — | — | — | — |
| Pharmaceuticals | pending | — | — | — | — |

**Score: 0/4 domains survive (2 of 4 tested).**

### The CEO's advancement table

Per PHASE_14_ADVANCEMENT_CRITERIA.md:
- 0/4 → Reject theory
- 1/4 → Local phenomenon
- 2/4 → Promising framework
- 3/4 → Strong theory
- 4/4 → Candidate M5

If aviation and pharmaceuticals also fail, the score is 0/4 → **Reject theory**.

If one of the remaining domains survives, the score is 1/4 → **Local phenomenon**.

### The honest assessment

The theory is in trouble. Two domains tested, two failures. The failure modes are different:
- Semiconductors: the theory works for 2 events (copper, high-k) with unambiguously high velocity, but misses 13/15 due to scaling events and threshold granularity.
- Telecom: the theory works for 0 events. The "re-rise" problem is structural — the formula cannot handle non-monotonic TRL.

The telecom failure is more damaging because it's not a granularity issue (which could be fixed by lowering the threshold). It's a structural issue: the formula's velocity term assumes monotonic TRL rise, and telecom capabilities don't rise monotonically.

### What would need to change (not authorized — formula is frozen)

If the formula were NOT frozen, the fix for telecom would be:
- Replace `max(dTRL/dt)` with `max(dTRL/dt, 0)` — clamp negative velocities to 0.
- Or: track each generation as a separate capability (WIRELESS_PROTOCOL_1G, WIRELESS_PROTOCOL_2G, etc.) so each rises monotonically.

But the formula IS frozen (Rule 1). The theory must stand or fall with the frozen formula. Telecom shows it falls.

### The next step

Two domains remain: aviation and pharmaceuticals. Per the CEO's directive, the project continues. If both fail, the theory is rejected (0/4). If one survives, the theory is a local phenomenon (1/4).

The honest expectation, based on the first two domains:
- Aviation has slow velocity (0.05-0.10 TRL/year, per INVARIANT_REGISTRY.md) — likely fails the > 0.20 threshold.
- Pharmaceuticals has non-monotonic TRL (clinical trial failures drop TRL) — likely fails the same way telecom did.

If both fail as expected, the theory is rejected. This would be the honest outcome — the theory works for Li-ion (and partially for photovoltaics) but does not generalize to structurally different domains.

---

## Artifacts

- Script: `scripts/run_telecom_backtest.py`
- Raw output: `evidence/observations/phase14_telecom_backtest.json`
- This document: `PHASE_14_TELECOM_RESULTS.md`
- Domain artifacts: `TELECOM_ONTOLOGY.md`, `TELECOM_EVENT_REGISTRY.md`, `TELECOM_TRAJECTORY_REGISTRY.md`, `TELECOM_BOTTLENECK_REGISTRY.md`
