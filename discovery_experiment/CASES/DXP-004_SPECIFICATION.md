# Discovery Experiment Specification — DXP-004

**Status:** FROZEN (pre-execution)
**Date:** 2026-08-08
**Engine commit:** f8e3f2ac136e3b03acc0b3314dc901fc614ae4a8
**Type:** CAPABILITY-CONTROL with QUANTITATIVE GROUND TRUTH (not a discovery test)
**Predecessors:** DXP-001 (NEG), DXP-002 (NEG), DXP-003 (positive-control recovery, filter problem NOT established)

---

## Purpose

DXP-004 is a known-positive mechanistic benchmark with a quantitative ground truth. The engine receives source and target documents but NOT the transfer, the mechanism, the direction, the magnitude, or the falsifier. These are frozen externally.

The experiment scores:
1. Did the engine identify the correct mechanism?
2. Did the engine identify the correct causal variable?
3. Did the engine produce the correct direction?
4. Did the engine produce a quantitatively useful prediction?
5. Did adversarial review correctly distinguish fatal vs nonfatal objections?
6. Does the prediction reproduce the independently known result?

This is the experiment that determines whether the adversarial gate is rejecting FALSE candidates correctly or TRUE candidates incorrectly.

---

## 1. Challenge Selection

**Source domain:** Ichthyology — shark skin denticle morphology and its hydrodynamic function

**Target domain:** Fluid mechanics — drag reduction surface design for water transport pipelines

**Why this challenge:**

1. **Quantitative ground truth exists:** Riblet surfaces (inspired by shark skin denticles) reduce turbulent drag by 5-10% in pipe flow. This is independently measured in published fluid mechanics literature (Bechert et al. 1997, Garcia-Mayoral & Jimenez 2011). The optimal riblet spacing is ~15 wall units (s+ ≈ 15), and the maximum drag reduction is ~8-10%.

2. **The transfer is NOT in the input:** The source document describes shark skin denticles in biological terms. The target document describes pipe drag in engineering terms. Neither references the other domain.

3. **Genuine lexical distance:** Shark biology uses "placoid scales," "dermal denticles," "ribbed structure," "mucus layer." Pipe fluid mechanics uses "Reynolds number," "friction factor," "pressure drop," "Darcy-Weisbach equation."

4. **Multiple plausible mechanisms:** The shark skin has several hydrodynamic features (riblets, mucus, flexibility) that could transfer to pipe design — testing whether the engine can distinguish the effective mechanism (riblets) from red herrings (mucus, flexibility).

5. **Prior-art richness:** Extensive published literature on riblet drag reduction. This makes prior-art checking meaningful.

### Frozen ground truth (NOT in engine input)

| Parameter | Known value | Source |
|---|---|---|
| Correct mechanism | Riblet geometry suppresses streamwise vorticity | Bechert et al. 1997 |
| Correct causal variable | Riblet spacing (s+) relative to wall units | Garcia-Mayoral & Jimenez 2011 |
| Correct direction | Drag DECREASES with riblet surface | Multiple experimental studies |
| Known magnitude | 5-10% drag reduction at optimal spacing | Bechert et al. 1997 |
| Optimal spacing | s+ ≈ 15 (dimensionless wall units) | Garcia-Mayoral & Jimenez 2011 |
| Known falsifier | Riblets with spacing outside 5-25 wall units produce NO drag reduction or drag increase | Multiple studies |

The engine's prediction will be scored against these values.

---

## 2. Frozen Input Package

### Document A: Source mechanism (shark skin)

A 1000-word technical description covering:
- Placoid scale (denticle) morphology: ribbed surface with longitudinal grooves
- The three-layer skin structure (enamel, dentine, pulp)
- Hydrodynamic function: drag reduction in turbulent flow
- The role of riblet spacing and height
- The mucus layer (red herring — lubricates but is not the primary drag mechanism)
- Skin flexibility (red herring — may help but is not the primary mechanism)
- Known failure modes (riblets ineffective at low Reynolds number, biofouling)

Does NOT reference pipes, fluid transport, or engineering applications.

### Document B: Target problem (pipe drag)

A 800-word description covering:
- Water transport pipeline (10 km, 0.5 m diameter, Re = 500,000)
- Current approach: smooth-walled pipes with chemical drag reducers
- Limitations: chemical cost, environmental concerns, smooth-wall friction factor floor
- Constraints: no chemicals, surface modification only, food-grade water, 20-year lifetime
- What is needed: a passive surface treatment that reduces pressure drop by at least 5%

Does NOT reference sharks, denticles, or biology.

### SHA-256 manifest

Both documents hashed and recorded before execution.

---

## 3. Information Boundary

### What is in the input
- Shark skin denticle morphology (ichthyology)
- Pipe drag problem (fluid mechanics)
- Physical constraints

### What is deliberately withheld
- Any reference connecting shark skin to pipe drag
- The expected transfer (riblet surface → drag reduction)
- The quantitative ground truth (5-10% reduction, s+ ≈ 15)
- The prior literature on riblet drag reduction
- The evaluation criteria and scoring rubric

### What constitutes "recovering the known transfer"
- Identifying riblet geometry (not mucus, not flexibility) as the key mechanism
- Predicting drag DECREASE (correct direction)
- Predicting a magnitude in the 5-10% range (correct order of magnitude)
- Identifying riblet spacing as the key design parameter

---

## 4. Controls (all run under identical information boundaries)

Same as DXP-003:
- C1: Engine (full pipeline)
- C2: Generic LLM (same model, no pipeline)
- C3: Retrieval-only
- C4: Human control — but this time the human is given ONLY the two documents and does NOT see the ground truth before producing their proposal
- C5: Matched null

### Human control protocol (revised from DXP-003)

The experimenter reads the two documents and produces a proposal. The ground truth (frozen above) is NOT consulted until AFTER the human proposal is recorded. This eliminates the confirmation bias from DXP-003.

---

## 5. Scoring Rubric

### For each condition (engine, generic LLM, human, retrieval, null):

| Criterion | Score | Ground truth |
|---|---|---|
| Transfer produced? | YES/NO | N/A |
| Correct mechanism identified? | YES/NO/PARTIAL | Riblet geometry (not mucus/flexibility) |
| Correct causal variable? | YES/NO/PARTIAL | Riblet spacing |
| Correct direction? | YES/NO | Drag DECREASES |
| Correct magnitude range? | YES/NO/PARTIAL | 5-10% reduction |
| Falsifiable prediction? | YES/NO | N/A |
| Prediction matches known result? | YES/NO/PARTIAL | 5-10% at optimal spacing |
| Survived adversarial? | YES/NO/N/A | N/A |

### Adversarial gate evaluation

For the engine specifically, evaluate each adversarial objection against the ground truth:

| Objection | Valid? | Why |
|---|---|---|
| (each HIGH-severity objection from the adversarial stage) | CORRECT/INCORRECT | Does the known literature support or refute this objection? |

This is the key diagnostic: if the adversarial gate raises objections that are REFUTED by the known literature, it is incorrectly killing true candidates. If the objections are SUPPORTED by the literature, it is correctly killing false candidates.

---

## 6. Pre-registration

Frozen before execution:
- Challenge (shark skin → pipe drag)
- Input documents
- Quantitative ground truth (mechanism, variable, direction, magnitude, falsifier)
- Scoring rubric
- Controls
- Adversarial evaluation protocol

Cannot be changed after execution.

---

## 7. Binary Outcome Classification

### For the ENGINE specifically:

**FILTER_CORRECT** — The adversarial gate correctly killed false/invalid candidates. The engine's candidates had real flaws that the literature confirms.

**FILTER_INCORRECT** — The adversarial gate incorrectly killed true/valid candidates. The engine's candidates were correct (matching ground truth), and the adversarial objections are refuted by the literature.

**FILTER_MIXED** — Some objections were valid, some were not. The gate needs calibration but is not fundamentally broken.

**GENERATOR_CORRECT** — The generator produced the right transfer with the right mechanism, direction, and magnitude.

**GENERATOR_INCORRECT** — The generator produced the wrong transfer, wrong mechanism, or wrong direction.

### For the overall capability ceiling:

Same matrix as DXP-003, plus the quantitative scoring.

---

## 8. Stop Conditions

Same as DXP-001/002/003, plus:
- The human control must NOT see the ground truth before producing their proposal
- The adversarial evaluation against ground truth must be performed after all outputs are recorded
- No modifying the engine, generator, or filter based on DXP-001/002/003
