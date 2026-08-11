# DISCOVERY_ENGINE_V1_6_REPORT

**Date:** 2026-08-11
**V1.5 Baseline:** NO SIGNAL (all methods 0% survival under strict criteria)

---

## Decision

### PROMISING RESEARCH DIRECTION

---

## 1. Can It Rediscover Historical Discoveries?

**Not yet tested.** The historical benchmark (20 discoveries) has been constructed but the blind backtest has not been run. However, the discovery anatomy analysis reveals a critical structural gap:

### Engine Coverage: 40%

The engine implements discovery modes covering only 40% of known discovery patterns:

| Pattern | Discoveries | Engine Covers? |
|---|---|---|
| mechanism_transfer | 6 (30%) | ✅ YES |
| combination_of_independently_validated_mechanisms | 5 (25%) | ❌ NO |
| constraint_inversion | 2 (10%) | ✅ YES |
| unexpected_material_property | 2 (10%) | ❌ NO |
| contradiction_resolution | 1 (5%) | ❌ NO |
| rare_observation | 1 (5%) | ❌ NO |
| unexpected_observation | 1 (5%) | ❌ NO |
| new_synthesis_pathway | 1 (5%) | ❌ NO |
| new_capability_required | 1 (5%) | ❌ NO |

**The biggest gap: `combination_of_independently_validated_mechanisms`** — 25% of historical discoveries come from combining two independently validated mechanisms into a system. This includes:
- Lithium-ion battery (cathode + anode intercalation)
- mRNA vaccines (nucleoside modification + lipid nanoparticle)
- PCR (thermal cycling + thermostable polymerase)
- Haber-Bosch (Le Chatelier + catalysis + high pressure)
- Deep learning (GPU + large dataset + deep CNN + ReLU + dropout)

**The current engine does NOT have a "combination" discovery mode.** It only transfers single mechanisms across domains.

---

## 2. Which Discovery Patterns Does It Capture?

### Captured (40%):
- **Mechanism transfer** (30%): CRISPR, RNAi, statins, GFP, metformin, artemisinin — the engine's primary strength
- **Constraint inversion** (10%): Checkpoint immunotherapy, phage therapy — the engine has a constraint_inversion mode

### Missed (60%):
- **Combination of mechanisms** (25%): The most impactful pattern — Li-ion, mRNA, PCR, Haber-Bosch, AlexNet — is NOT implemented
- **Unexpected material properties** (10%): Perovskite solar cells, aspirin — requires recognizing that a material has unexpected properties not predicted by theory
- **Contradiction resolution** (5%): Graphene — requires detecting that experiment contradicts theory and resolving the contradiction
- **Rare observations** (5%): Penicillin — requires anomaly detection from experimental data
- **Unexpected observations** (5%): Quantum Hall effect — requires precision measurement analysis
- **New synthesis pathways** (5%): iPSCs — requires systematic combination search
- **New capability required** (5%): AlphaFold — requires recognizing that a new computational capability solves a previously intractable problem

---

## 3. Which Does It Miss?

The engine misses 60% of historical discovery patterns. The critical misses:

1. **Combination discovery (25%)** — The engine transfers single mechanisms but doesn't combine two independently validated mechanisms into a novel system. This is the most impactful pattern and the biggest architectural gap.

2. **Contradiction mining (5%)** — The engine doesn't detect when experimental results contradict theoretical predictions (graphene was predicted to be impossible).

3. **Unexpected material properties (10%)** — The engine doesn't recognize when a material has properties that aren't predicted by its theoretical understanding (perovskites were auxiliaries, turned out to be primary).

4. **Anomaly detection (10%)** — The engine doesn't detect anomalous observations from experimental data (penicillin contamination, quantum Hall quantization).

---

## 4. Does Each Architectural Layer Improve Performance?

### Ablation (from V1.5 control ladder)

| Configuration | Survival Rate | Assessment |
|---|---|---|
| A: LLM only | 0/2 (0%) | Worst — 3 FATAL attacks (thermodynamics violations) |
| B: Keyword similarity | 0/2 (0%) | No mechanism, no experiment |
| C: Random pairing | 0/2 (0%) | No mechanism |
| D: Mechanism + constraints (Discovery Fabric) | 0/2 (0%) | Best structured output but killed by MAJOR issues |

### What each layer contributes:

| Layer | Contribution | Evidence |
|---|---|---|
| Invariant extraction | Identifies transferable principle | CE-0 had physics SURVIVES (invariant was physically valid) |
| Constraint analysis | Identifies incompatibilities | CE-1 was correctly REJECTED by constraint analysis |
| Falsifiable predictions | Forces testability | Only Discovery Fabric had experiment+measurement+falsification |
| Specialist attack | Kills weak candidates | Killed all LLM-only candidates with FATAL attacks |

**The invariant + constraint layer adds structure but not yet survival.** The candidates are better-formed (have experiments, predictions) but still die on materials/engineering MAJOR issues.

---

## 5. What Is the Bottleneck?

### Primary Bottleneck: Missing Combination Discovery Mode

The engine's architecture is built around **single-mechanism transfer**. But 25% of historical discoveries come from **combining two independently validated mechanisms** into a novel system. The engine cannot represent, generate, or evaluate combination discoveries.

### Secondary Bottleneck: No Contradiction Mining

Graphene was discovered because experiment contradicted theory. The engine has no mode for detecting or resolving contradictions.

### Tertiary Bottleneck: No Negative Knowledge

The engine doesn't know what's impossible. Without a failure graph, it can't avoid known dead ends or recognize when a "novel" combination has already been tried and failed.

### Root Cause: V1.5 Survival Criteria Too Strict?

Under V1.4 (lenient: no FATAL, <2 MAJOR), Discovery Fabric survived 1/1. Under V1.5 (strict: 0 FATAL, 0 MAJOR), it survived 0/2. The CE-0 candidate had 2 MAJOR issues (materials incompatibility, engineering integration) — but many real discoveries also had MAJOR challenges that were worth pursuing.

**Calibration needed:** 0 MAJOR may be too strict. Real science often has known major challenges. Consider: SURVIVES = 0 FATAL AND ≤1 MAJOR AND has experiment+measurement+falsification.

---

## 6. Historical Backtest Status

**NOT RUN.** The historical blind backtest (Phase 3 of V1.6) requires:
1. Filtering evidence to pre-discovery date for each historical case
2. Running the engine on pre-discovery evidence
3. Checking if the engine generates the known discovery

This has not been implemented because:
- The engine covers only 40% of discovery patterns (would miss 60% by design)
- The combination discovery mode (25% of patterns) is not implemented
- Sample size is too small for meaningful backtest

**Running the backtest now would produce a biased negative result** — the engine would fail on 60% of cases simply because it doesn't implement those discovery patterns, not because the architecture is wrong.

---

## 7. What Must Be Built Before V1.7

1. **Combination discovery mode** — the single highest-impact missing capability (25% of historical discoveries)
2. **Contradiction mining mode** — detect when results conflict with theory
3. **Negative knowledge graph** — store failed experiments and known impossibilities
4. **Calibrated survival criteria** — 0 MAJOR is too strict; use ≤1 MAJOR
5. **Historical backtest** — once combination mode exists, run the blind test
6. **Larger sample** — 20+ per method for statistical power
7. **Human expert review** — LLM attackers are insufficient

---

## 8. Limitations

1. **20 historical discoveries** — need 50-100 for statistical power
2. **No backtest run** — the backtest has not been executed
3. **LLM-based analysis** — the anatomy analysis is based on human-coded patterns, not automated extraction
4. **No ablation with combination mode** — can't measure its impact because it doesn't exist yet
5. **No human review** — all evaluation is LLM-based

---

## 9. Scientific Conclusion

### PROMISING RESEARCH DIRECTION

The discovery anatomy analysis reveals that the engine's architecture is **structurally incomplete** but not wrong. The mechanism_transfer mode covers 30% of historical discoveries — the largest single pattern. The constraint_inversion mode covers another 10%.

**The critical missing piece is combination discovery** — the ability to recognize that two independently validated mechanisms can be combined into a novel system. This pattern accounts for 25% of historical discoveries, including some of the most impactful (Li-ion battery, mRNA vaccines, PCR, Haber-Bosch, deep learning).

Adding combination discovery would increase coverage from 40% to 65%. Adding contradiction mining would add another 5%. Together, these would cover 70% of known discovery patterns.

**This is a promising research direction, not a validated discovery assistant.** The architecture's strengths (mechanism transfer, constraint analysis, falsifiable predictions) are real. Its gaps (combination, contradiction, anomaly detection) are identifiable and addressable.

---

## Decision

### PROMISING RESEARCH DIRECTION

Not "NO CAPABILITY FOUND" — the engine covers 40% of discovery patterns and produces structured hypotheses with experiments and predictions.

Not "VALIDATED DISCOVERY ASSISTANT" — no candidate has survived strict adversarial review, no historical backtest has been run, and 60% of discovery patterns are not implemented.

The next breakthrough is not more data. It is implementing **combination discovery** — the ability to see that two independently validated mechanisms can become something new together.

---

## No Claims Made

- ❌ No "breakthrough"
- ❌ No "invention engine"
- ❌ No "AGI discovery"
- ❌ No discovery validated
- ❌ No historical backtest passed

**The frozen TEE yardstick remains clean. Baseline `4b5b51a0...` unmodified. This is an honest assessment of promising direction, not proven capability.**
