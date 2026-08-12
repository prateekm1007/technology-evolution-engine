# DISCOVERY_ENGINE_V1_5_VALIDATION_REPORT

**Date:** 2026-08-11
**V1.4 Baseline:** FROZEN (hash `043ed456...`)
**Question:** Does invariant + constraint reasoning outperform simpler baselines?

---

## Decision

### NO SIGNAL

Under strict V1.5 survival criteria (no FATAL, no MAJOR, must have experiment + measurement + falsification), no method produced surviving candidates. Discovery Fabric does not outperform baselines at this sample size.

---

## 1. Dataset

| Metric | Value |
|---|---|
| Mechanisms | 40 (8 domains, 5 per domain) |
| Invariants | 8 successful extractions |
| Evidence pool | 7,032 scientific works (frozen baseline) |
| Domains | materials, energy, biotechnology, computing, mechanical, chemical, environmental, neuroscience |

## 2. Methods

| Method | Description |
|---|---|
| CONTROL_A (random) | Random domain pairing, no mechanism reasoning |
| CONTROL_B (keyword) | Keyword similarity between domains |
| CONTROL_D (LLM-only) | LLM generates hypothesis directly from abstract, no mechanism graph |
| CONTROL_E (Discovery Fabric) | Invariant extraction + constraint analysis + falsifiable prediction |
| Hard nulls | Scientifically plausible but physically impossible |

All methods received the same evidence pool and were attacked by the same blind specialist attackers.

## 3. Controls

All cases were **blinded** — attackers could not see:
- Generator type (random/keyword/LLM/Discovery Fabric/null)
- Candidate vs null status
- Model used

Attackers evaluated: physics validity, materials feasibility, engineering manufacturability.

## 4. Generated Hypotheses

| Method | Generated |
|---|---|
| Random | 2 |
| Keyword | 2 |
| LLM-only | 2 |
| Discovery Fabric | 2 |
| Hard nulls | 2 |
| **Total** | **10** |

## 5. Survival Statistics

| Method | Total | Survived | Killed | Survival Rate |
|---|---|---|---|---|
| Random | 2 | 0 | 2 | 0% |
| Keyword | 2 | 0 | 2 | 0% |
| LLM-only | 2 | 0 | 2 | 0% |
| **Discovery Fabric** | 2 | **0** | 2 | **0%** |
| Hard nulls | 2 | 0 | 2 | 0% |

**No method produced surviving candidates under V1.5 strict criteria.**

## 6. Null Rejection

| Metric | Value |
|---|---|
| Hard nulls generated | 2 |
| Hard nulls killed | 2 |
| Null rejection rate | 100% |
| False positive rate | 0% |

## 7. Failure Analysis

### Why Discovery Fabric Failed (V1.5 vs V1.4)

V1.4 had 1/1 survival. V1.5 has 0/2 survival. The difference:

**V1.4** used lenient criteria: SURVIVES if fatal=0 and major<2.
**V1.5** uses strict criteria: SURVIVES only if fatal=0 AND major=0 AND has_experiment AND has_measurement AND has_falsification.

### CE-0 (Discovery Fabric — closest to survival)
- Physics: SURVIVES (self-healing concept is physically valid)
- Materials: MAJOR (self-healing materials incompatible with battery electrolyte)
- Engineering: MAJOR (manufacturing integration not addressed)
- Had experiment, measurement, and falsification: YES
- **Killed by 2 MAJOR issues**

### CE-1 (Discovery Fabric — rejected)
- Transfer was rejected by constraint analysis during generation
- Produced empty hypothesis → killed

### LLM-only (worst performer)
- CD-1: 3 FATAL attacks (thermodynamics violation, materials impossible, engineering impossible)
- No experiment, no measurement, no falsification

### Hard Nulls (correctly killed)
- NULL-0: 1 MAJOR (killed by strict criteria)
- NULL-1: 2 MAJOR (killed by strict criteria)
- Both had experiments but contained hidden flaws

## 8. Historical Backtest

**NOT CONSTRUCTED.** The historical blind discovery benchmark has not been built. This is a required future test.

## 9. Limitations

1. **Tiny sample size** — 2 cases per method. No statistical significance possible.
2. **Only 8 invariants** — Discovery Fabric's advantage may require more invariant coverage
3. **3 specialist attackers** (physics, materials, engineering) — biology and chemistry not included
4. **LLM-based attackers** — not human experts. May be overly strict or lenient.
5. **No historical backtest** — cannot determine if system would have discovered known connections
6. **V1.5 strict criteria** may be too strict — 0 MAJOR is very demanding. Real science often has known major challenges that are worth pursuing.

## 10. Scientific Conclusion

### NO SIGNAL

Under strict V1.5 survival criteria, Discovery Fabric does not outperform baselines. All methods scored 0% survival. The strict criteria (no FATAL, no MAJOR, must have full experiment design) killed every candidate.

### What the data shows

- Discovery Fabric candidates are **more structured** (have experiments, measurements, falsifications) than random/keyword/LLM-only
- Discovery Fabric CE-0 was the **closest to survival** (physics SURVIVES, killed by materials/engineering MAJOR issues)
- LLM-only was the **worst performer** (3 FATAL attacks on CD-1)
- Hard nulls were **correctly killed** (100% rejection rate)

### What the data does NOT show

- Discovery Fabric does NOT produce more surviving candidates than baselines (0% vs 0%)
- The advantage seen in V1.4 (1/1 survival) does NOT replicate under strict criteria
- No statistical evidence of discovery advantage

### Interpretation

The V1.4 "PRELIMINARY DISCOVERY SIGNAL" was likely an artifact of:
1. **Lenient survival criteria** (allowed MAJOR issues)
2. **Tiny sample size** (1 candidate)
3. **No control comparison** (V1.4 had no LLM-only baseline)

Under V1.5 strict criteria with control comparison, the signal disappears.

**This is honest negative evidence.** The architecture does not yet demonstrate a reproducible advantage over simpler methods.

---

## What Must Happen Before V1.6

1. **Larger sample** — 20+ per method for statistical power
2. **More invariants** — 50+ for broader transfer coverage
3. **Calibrated survival criteria** — 0 MAJOR may be too strict; consider "no FATAL, ≤1 MAJOR"
4. **Historical backtest** — the ultimate validation
5. **Human expert review** — LLM attackers are insufficient
6. **Ablation** — which component (invariants, constraints, predictions) contributes?

---

## Final Statement

The scientific question was: "Does invariant + constraint reasoning outperform simpler baselines?"

**Answer: Not yet.** At this sample size with these criteria, no method produces surviving candidates. Discovery Fabric generates more structured hypotheses (with experiments and falsifications) but does not survive adversarial attack more often than baselines.

The V1.4 "PRELIMINARY DISCOVERY SIGNAL" is retracted under strict criteria.

**DISCOVERY ENGINE = UNPROVEN HYPOTHESIS**

The frozen TEE yardstick remains clean. Baseline `4b5b51a0...` unmodified. No evidence manufactured. This is an honest negative result.
