# DXP-003 Final Verdict

**Experiment:** DXP-003 (positive-control diagnostic)
**Date:** 2026-08-08
**Engine commit:** f8e3f2ac136e3b03acc0b3314dc901fc614ae4a8
**Challenge:** Bat echolocation signal processing → adaptive radar waveform design for clutter rejection

---

## Binary Outcome: **NOT DISCOVERY** (but diagnostically decisive)

---

## Capability Ceiling Matrix

| Condition | Transfer produced? | Non-trivial? | Survived adversarial? | Falsifiable? | Physically plausible? |
|---|---|---|---|---|---|
| **Engine (full pipeline)** | YES | 1/3 NON_TRIVIAL | 0/3 survived | YES (but blocked) | Not assessed (blocked) |
| **Generic LLM** | YES | Likely non-trivial | N/A (no adversarial) | YES | YES |
| **Retrieval-only** | NO (entity overlap only) | N/A | N/A | N/A | N/A |
| **Human control** | YES | YES (explicitly non-obvious) | N/A | YES | YES |
| **Matched null** | NO (no source) | N/A | N/A | N/A | N/A |

### Diagnosis: **GENERATOR_DEFICIT + FILTER_PROBLEM**

The engine, generic LLM, and human all produced the same core transfer (adaptive pulse duration based on target range). But:

1. **The generic LLM produced a specific, quantified, falsifiable proposal** — adaptive pulse duration with three range-dependent modes, quantitative false alarm reduction prediction (40-60%), and a clear falsifier. This is exactly the expected transfer.

2. **The human control produced the same transfer** — adaptive pulse duration + Doppler compensation, with quantitative predictions and a falsifier.

3. **The engine produced the same core transfer** — adaptive pulse duration based on target range — BUT all 3 hypotheses were killed at the adversarial gate.

### Why the engine failed where controls succeeded

**Filter problem:** The adversarial gate killed H-001 (adaptive pulse duration) with:
- [HIGH] FRAGILE_ASSUMPTION: "Range estimation accuracy is insufficient for reliable pulse adaptation"
- [HIGH] CONTRADICTS_KNOWN: "Pulse duration changes inherently increase range-Doppler coupling"

These criticisms are technically valid concerns, but they are **not fatal flaws**:
- Range estimation accuracy: The radar already estimates range (it's a surveillance radar). The criticism overstates the difficulty.
- Range-Doppler coupling: This is a known issue with LFM waveforms, but it's manageable with Doppler processing. The criticism treats a known engineering challenge as a fundamental contradiction.

The adversarial gate is **too aggressive** for this challenge. It treats engineering challenges as fundamental flaws, killing candidates that are practically viable.

**Generator quality:** 2/3 engine hypotheses were classified as PARAPHRASED_IN_INPUT (rediscovery), and 1/3 was NON_TRIVIAL_TRANSFER. The generator produces the right transfer (adaptive pulse duration) but doesn't quantify it as well as the generic LLM or human control.

### What this tells us

| Hypothesis | Evidence |
|---|---|
| H1: Challenge mismatch | ❌ REJECTED — the challenge is solvable (generic LLM and human both solved it) |
| H2: Generator weakness | ⚠️ SUPPORTED — the generator produces the right transfer but doesn't quantify it well |
| H3: Over-aggressive filter | ✅ CONFIRMED — the filter killed a viable candidate with engineering concerns treated as fatal flaws |
| H4: Generic LLM limitation | ❌ REJECTED — the generic LLM produced a strong proposal |
| H5: Approaching North Star | ❌ NOT YET — engine didn't survive, but the gap is now diagnosed |

---

## Failure Map

```
Stage                          Status    Detail
────────────────────────────── ──────── ──────────────────────────────────────
representation (extraction)   PASS      24 nodes, 16 edges, 5 failures
abstraction                   PASS      "Adaptive signal processing based on
                                         environmental feedback enables precise
                                         target detection and discrimination"
transfer                      PASS      Explicit mapping produced
hypothesis generation         PARTIAL   Right transfer, but 2/3 are paraphrases
novelty (rediscovery)         MIXED     2/3 PARAPHRASED, 1/3 NON_TRIVIAL
adversarial filtering         FAIL      All killed — but with over-aggressive
                                         criticisms (engineering challenges treated
                                         as fundamental flaws)
prediction                    BLOCKED   No hypotheses survived
experiment                    BLOCKED
accuracy                      BLOCKED
```

---

## DXP-001 → DXP-002 → DXP-003 comparison

| Dimension | DXP-001 | DXP-002 | DXP-003 |
|---|---|---|---|
| Geometry | biology → control | entomology → materials | bioacoustics → radar |
| Challenge hostile? | Yes (no-ML) | No | No |
| Engine transfer? | YES | YES | YES |
| Engine non-trivial? | 3/3 (100%) | 1/4 (25%) | 1/3 (33%) |
| Engine survived? | 0/3 | 0/4 | 0/3 |
| Generic LLM transfer? | Not tested | Not tested | YES |
| Generic LLM viable? | N/A | N/A | YES |
| Human transfer? | Not tested | Not tested | YES |
| Human viable? | N/A | N/A | YES |
| Primary failure | TARGET_CONSTRAINT | MECHANISTIC_DEFECT | FILTER_PROBLEM |
| Diagnosis | Challenge mismatch | Generator weakness | Over-aggressive filter |

---

## What this experiment proves

### Proves
1. **The challenge is solvable** — both the generic LLM and the human control produced the expected transfer (adaptive pulse duration based on target range). This is NOT a challenge problem.

2. **The engine produces the right transfer** — H-001 (adaptive pulse duration) is the same mechanism that the generic LLM and human identified. The engine's extraction → abstraction → transfer pipeline works correctly.

3. **The adversarial gate is over-aggressive** — it killed a viable candidate (H-001) with criticisms that are engineering challenges, not fundamental flaws. "Range estimation accuracy is insufficient" is wrong for a surveillance radar that already estimates range. "Pulse duration changes inherently increase range-Doppler coupling" is a known issue with known mitigations.

4. **The generator is somewhat weak** — 2/3 hypotheses were paraphrases, and the engine's proposals were less quantified than the generic LLM's. But the generator DID produce the right transfer.

5. **H2 is supported but the picture is more nuanced than "generator weakness"** — the generator produces the right transfer but the adversarial filter kills it with over-aggressive criticism. The bottleneck is BOTH generator quality (paraphrases) AND filter aggressiveness (engineering challenges treated as fatal flaws).

### Does NOT prove
- That the engine can produce a candidate that survives adversarial analysis
- That the engine can produce a falsifiable prediction that reaches experiment
- Discovery capability

---

## Honest assessment

**The engine's pipeline works: it extracts, abstracts, transfers, and generates the right hypothesis.** The generic LLM, given the same documents, produces a stronger proposal (more quantified, more specific). The human control produces the same core transfer.

**The adversarial gate is the immediate bottleneck for DXP-003.** It killed a viable candidate with criticisms that overstate engineering challenges as fundamental contradictions. A human reviewer would not have killed H-001 for "range estimation accuracy" — that's a known, solvable problem in radar.

**The generator is a secondary bottleneck.** It produces the right transfer but doesn't quantify it as well as the generic LLM. 2/3 hypotheses were paraphrases. The generator needs to go deeper into the mechanism and produce more specific, quantified predictions.

### What would need to change (for future consideration)

1. **Adversarial gate calibration:** The gate should distinguish between:
   - Fundamental flaws (violates physics, contradicts established principles) → KILL
   - Engineering challenges (requires better hardware, more computation, tighter tolerances) → FLAG but don't KILL
   - Missing quantification (unquantified effect sizes) → FLAG but don't KILL

2. **Generator depth:** The generator should produce quantified predictions (specific numbers, not just "will improve"). The generic LLM did this naturally; the engine's pipeline dilutes the quantification through multiple stages.

3. **Constraint-awareness:** The generator should check target constraints before producing hypotheses (carried over from DXP-001/002).

These are engine improvements, not substrate improvements. The substrate is working correctly.

---

## Recommendation

1. **The adversarial gate needs calibration.** This is now the most immediate bottleneck. The gate is too aggressive for engineering problems where "challenging but solvable" is different from "fundamentally flawed."

2. **The generator needs depth.** The generic LLM outperforms the engine's multi-stage pipeline on quantification. This suggests the pipeline's decomposition (extract → abstract → transfer → hypothesize) may be losing quantitative detail.

3. **Run DXP-004 only after the gate is recalibrated.** Running the same engine on a fourth challenge would likely produce the same result (all killed at adversarial).

4. **The positive-control design was successful.** It distinguished between challenge problem, generator deficit, and filter problem. The diagnosis is now actionable.

---

## North Star status

```
DXP-001:  NOT DISCOVERY (TARGET_CONSTRAINT_DEFECT — challenge hostile)
DXP-002:  NOT DISCOVERY (MECHANISTIC_DEFECT + GENERATION_DEFECT — shallow analogies)
DXP-003:  NOT DISCOVERY (FILTER_PROBLEM — over-aggressive adversarial gate
          killed a viable candidate that both generic LLM and human control produced)

Diagnosis:
  Challenge problem?     NO (controls succeeded)
  Generator deficit?     PARTIAL (right transfer, but shallow/paraphrased)
  Filter problem?        YES (over-aggressive — engineering challenges treated as fatal)
  LLM limitation?        NO (generic LLM produced strong proposal)
  Approaching North Star? NOT YET (but the gap is now precisely diagnosed)

The engine produces the right transfer. The filter kills it.
The next improvement should be adversarial gate calibration + generator depth.

Discovery capability:  NOT ESTABLISHED
North Star:            NOT ACHIEVED

But the path to the North Star is now visible:
  calibrate the adversarial gate → let viable candidates survive →
  produce quantified predictions → test against reality
```
