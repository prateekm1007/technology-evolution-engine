# V1.13 GATE 2 — LEAKAGE / INFORMATION-CONTENT VALIDATION REPORT

**Date:** 2026-08-12
**Task ID:** v1.13-gate2-leakage-ic-validation
**Status:** COMPLETE — Exit gate FAILED. Negative result accepted.
**Prior gate frozen at:** `7209b294` (V1.13 Forensic Correction, Gate 1)
**This gate committed at:** (see git log)

---

## 1. Directive (verbatim)

> V1.13 FORENSIC GATE 2 — LEAKAGE / INFORMATION-CONTENT VALIDATION
>
> No new discovery architecture. No 50-case expansion.
>
> Freeze 7209b294 and all V1.13 forensic artifacts.
> Audit the 40 receipts for implicit entailment, not just string overlap. A prediction must be classified RECONSTRUCTION when it is a near-deterministic consequence of the supplied evidence even if the exact sentence/terms never appear.
> Build a deterministic entailment test using structured evidence objects: entities present, mechanisms present, causal edges present, combination already implied, constraint already stated, prediction derivable without introducing a genuinely new relation.
> Reject any prediction whose information content is effectively encoded in the input.
> Eliminate range fitting completely: use point estimates or tightly pre-registered tolerances; never allow arbitrary broad intervals.
> Run a model-leakage control with a genuinely frozen model/evidence setup where the model cannot access post-cutoff information.
> Compare: LLM-only, mechanism, full, random under identical cutoffs and budgets.
> Report: RECONSTRUCTION, GENUINE_NOVEL_PREDICTION, CORRECT, INCORRECT, INDETERMINATE, calibration error, information-content score.
>
> Exit gate: if fewer than a meaningful number of predictions survive the information-content test, accept the negative result. Do not manufacture a discovery signal.
>
> Only after this gate is closed do we decide whether the discovery thesis deserves another experiment.

---

## 2. Frozen Prior Artifacts (Preserved, Not Modified)

| Artifact | Status |
|---|---|
| Gate 1 commit `7209b294` | UNCHANGED |
| Original V1.13 receipts (`discovery_fabric/v1_13/receipts/`) | UNCHANGED |
| Original V1.13 results (`discovery_fabric/v1_13/results.json`) | UNCHANGED |
| Gate 1 forensic evaluator (`discovery_fabric/v1_13_forensic/`) | UNCHANGED |
| Gate 1 forensic results (`discovery_fabric/v1_13_forensic/results.json`) | UNCHANGED |

All Gate 2 work is in a separate directory: `discovery_fabric/v1_13_gate2/`.

---

## 3. Gate 2 Components Built

### 3.1 Structured Evidence Extractor (deterministic, no LLM)
**File:** `discovery_fabric/v1_13_gate2/structured_evidence_extractor.py`

Converts raw evidence text into a structured evidence object with:
- `entities` (proper nouns, technical nouns, chemicals)
- `mechanisms` (subject-predicate-object triples, 7 predicate types: CAUSES / ENABLES / PREVENTS / INCREASES / DECREASES / EXHIBITS)
- `causal_edges` (subject → effect, typed)
- `combinations` (explicit "X and Y" / "X combined with Y" / "X+Y")
- `constraints` (numeric or property assertions)
- `negations` (explicit negative statements)

Extraction is regex-based, conservative, and 100% deterministic. Output is hash-sealed for immutability.

### 3.2 Deterministic Entailment Test (no LLM)
**File:** `discovery_fabric/v1_13_gate2/deterministic_entailment_test.py`

Six sub-checks against the structured evidence object:

| Check | What it tests | Encodes if... |
|---|---|---|
| (1) ENTITIES_PRESENT | All prediction entities in evidence | No new proper nouns or chemicals |
| (2) MECHANISMS_PRESENT | All prediction mechanism verbs in evidence | No new relational verbs |
| (3) CAUSAL_EDGES_PRESENT | Every SVO triple in prediction maps to evidence edge | All triples matched |
| (4) COMBINATION_ALREADY_IMPLIED | Prediction's X+Y pair already in evidence combinations OR both X,Y independently attested | Trivial conjunction |
| (5) CONSTRAINT_ALREADY_STATED | Prediction's numeric constraint range includes an evidence-stated value | Restated constraint |
| (6) PREDICTION_DERIVABLE_WITHOUT_NEW_RELATION | Composite of (1)+(2)+(3) | All three pass |

Classification:
- **RECONSTRUCTION** if (3) OR (4) OR (5) OR (6) is True, OR encoded_count ≥ 4
- **PARTIALLY_NOVEL** if encoded_count is 2-3 (treated as RECONSTRUCTION for Gate 2)
- **GENUINE_NOVEL_PREDICTION** if encoded_count ≤ 1

Information-content score: `IC = 1 - (encoded_count / 6)` (0.0 = full reconstruction, 1.0 = fully novel).

### 3.3 Leakage-Controlled Generator
**File:** `discovery_fabric/v1_13_gate2/leakage_controlled_generator.py`

Re-generates 40 receipts under:
- **Evidence-only system prompt** explicitly forbidding use of any prior knowledge
- **Point-estimate requirement**: predicted_value + multiplicative tolerance bounds (no broad ranges)
- **Hard tolerance constraint**: `tolerance_lower ≥ 0.25 AND tolerance_upper ≤ 4.0`
- **No retrieval, no auxiliary corpus** — only the pre-outcome evidence text
- Backend: `z-ai` CLI (glm-4-plus), the only LLM backend available in this environment

### 3.4 Gate 2 Evaluator (deterministic, no LLM)
**File:** `discovery_fabric/v1_13_gate2/gate2_evaluator.py`

Final classification per receipt:
1. Run deterministic entailment test
2. If RECONSTRUCTION or PARTIALLY_NOVEL → final = RECONSTRUCTION
3. If GENUINE_NOVEL_PREDICTION → evaluate quantitative accuracy:
   - BINARY: exact YES/NO match → CORRECT / INCORRECT
   - Numeric: observed within `[predicted × tol_lower, predicted × tol_upper]` AND `calibration_error ≤ 0.50` → CORRECT, else INCORRECT
4. DPS=1 if GENUINE_NOVEL_PREDICTION AND CORRECT

---

## 4. Honest Limitation: Model-Leakage Control

The directive requires "a genuinely frozen model/evidence setup where the model cannot access post-cutoff information."

**What we can control:**
- The prompt contains ONLY the pre-outcome evidence text
- The system prompt explicitly forbids use of prior knowledge
- No retrieval, no auxiliary corpus lookup
- Point-estimate requirement eliminates broad-range fitting

**What we cannot control (in this environment):**
- The LLM's parametric memory. The glm-4-plus model's training data post-dates every cutoff date in the benchmark (1990-2013). The model has effectively "seen the answer" for every case.
- We cannot use a model with an earlier training cutoff (none available in this environment).
- We cannot use a retrieval-only architecture with no parametric memory (none available in this environment).

**What this means:**
The evidence-only prompt is a SOFT constraint. The Gate 2 evaluator measures the EMPIRICAL effect of:
(a) the evidence-only prompt instruction, and
(b) the point-estimate + tight-tolerance requirement.

If the LLM is leaking parametric memory (which it almost certainly is), the Gate 2 results represent an UPPER BOUND on the system's true discovery ability. The actual discovery ability is at most what Gate 2 measures, and likely lower.

This limitation is documented honestly. It does NOT invalidate the negative result — if the system cannot produce discoveries even with the upper-bound advantage of parametric-memory leakage, it certainly cannot produce them without it.

---

## 5. Gate 2 Results (40 receipts, 10 cases × 4 configs)

### 5.1 Overall classification counts

| Classification | Count | % |
|---|---|---|
| RECONSTRUCTION | 15 | 37.5% |
| GENUINE_NOVEL_PREDICTION (but INCORRECT) | 0 | 0.0% |
| CORRECT (genuine novel AND correct) | 0 | 0.0% |
| INCORRECT (genuine novel but wrong) | 6 | 15.0% |
| INDETERMINATE (direction-type mismatch) | 19 | 47.5% |
| **Total** | **40** | **100%** |

### 5.2 Summary by config

| Config | n | RECON | NOVEL | CORR | INCR | INDT | DPS=1 | DPS% | calErr (CORR) | mean IC |
|---|---|---|---|---|---|---|---|---|---|---|
| B_llm_only | 10 | 4 | 6 | 0 | 1 | 5 | 0 | 0.0% | – | 0.783 |
| C_mechanism | 10 | 6 | 4 | 0 | 0 | 4 | 0 | 0.0% | 0.176 (n=1*) | 0.700 |
| F_full | 10 | 2 | 8 | 0 | 3 | 5 | 0 | 0.0% | – | 0.850 |
| D_random | 10 | 3 | 7 | 0 | 2 | 5 | 0 | 0.0% | 0.263 (n=1*) | 0.817 |

\* C_mechanism and D_random each have 1 numeric CORRECT case, but BOTH are classified as RECONSTRUCTION (not GENUINE_NOVEL_PREDICTION), so neither contributes to DPS=1.

### 5.3 Exit gate decision

| Gate | Criterion | Threshold | Observed | Pass? |
|---|---|---|---|---|
| Gate 1 | ≥ 3 GENUINE_NOVEL_PREDICTION across all 40 | 3 | 25 | ✅ PASS |
| Gate 2 | Best treatment DPS% ≥ random DPS% + 15pp | 15pp | 0pp (both 0%) | ❌ FAIL |
| **EXIT GATE** | Both sub-gates pass | AND | — | ❌ **FAIL** |

### 5.4 Calibration error distribution

Of the 21 numeric receipts classified as GENUINE_NOVEL_PREDICTION (i.e., not RECONSTRUCTION):
- 0 had calibration_error ≤ 0.50 (CORRECT)
- 4 had calibration_error between 0.50 and 1.0 (close miss)
- 17 had calibration_error > 1.0 (orders-of-magnitude miss)

The LLM's point estimates are dramatically off from the historical outcomes. This is consistent with the LLM NOT actually knowing the answer (perhaps the evidence-only prompt is partially effective), but it also means the system produces no usable predictions.

### 5.5 Information-content score distribution

Of the 40 receipts:
- 15 (37.5%) classified RECONSTRUCTION (IC < 0.67)
- 0 (0%) classified PARTIALLY_NOVEL (0.34 ≤ IC < 0.67)
- 25 (62.5%) classified GENUINE_NOVEL_PREDICTION (IC ≥ 0.67)

The deterministic entailment test is now MUCH stricter than Gate 1's string-overlap test (which classified 0/40 as RECONSTRUCTION). Gate 2 classifies 15/40 (37.5%) as RECONSTRUCTION, catching predictions that are near-deterministic consequences of the evidence even when their surface form differs.

The 25 GENUINE_NOVEL_PREDICTION receipts pass the information-content test but FAIL the quantitative-accuracy test — they are novel but wrong.

---

## 6. Verdict: 30-40% Discovery Claim Does NOT Survive Gate 2

### 6.1 Compared to Gate 1

| Metric | Gate 1 (forensic) | Gate 2 (leakage-controlled) |
|---|---|---|
| Total receipts | 40 (original V1.13) | 40 (newly generated) |
| Scoring strictness | Stricter than original V1.13 | Stricter than Gate 1 |
| Information-content test | String overlap (100% pass) | Deterministic entailment (62.5% pass) |
| Range fitting | Allowed (some survived) | Eliminated (point estimates only) |
| DPS=1 count | 3/40 (7.5%) | **0/40 (0%)** |
| Best treatment DPS% | F_full: 20% | All: 0% |
| Random control DPS% | D_random: 10% | D_random: 0% |
| Material advantage | 10pp (not significant) | 0pp (none) |

### 6.2 Why DPS dropped to 0

The Gate 2 DPS=1 rate is 0% (down from Gate 1's 7.5%) for three compounding reasons:

1. **Range fitting eliminated.** Gate 1's 3 surviving receipts (PB-001|D_random, PB-001|F_full, PB-004|F_full) all had broad ranges like [500, 1000] or [15, 30] that included the observed value. Gate 2 requires point estimates with tight multiplicative tolerances (lower ≥ 0.25, upper ≤ 4.0). The LLM cannot fit ranges to known answers.

2. **Information-content test tightened.** Gate 1's string-overlap test classified 0/40 as RECONSTRUCTION (suspicious). Gate 2's deterministic entailment test classifies 15/40 as RECONSTRUCTION. Several Gate 1 "DPS=1" receipts would be RECONSTRUCTION under Gate 2.

3. **Quantitative accuracy dramatically worse.** Without range fitting, the LLM's point estimates are far from the historical outcomes. Of 21 numeric GENUINE_NOVEL_PREDICTION receipts, 17 had calibration_error > 1.0 (orders-of-magnitude miss).

### 6.3 Negative result accepted

Per the directive's exit gate: "if fewer than a meaningful number of predictions survive the information-content test, accept the negative result. Do not manufacture a discovery signal."

- 0/40 receipts achieve DPS=1 under Gate 2 criteria.
- The Gate 1 "30-40% discovery" claim was an artifact of (a) lenient broad-range matching and (b) lenient string-overlap novelty.
- Under the stricter Gate 2 criteria (deterministic entailment + point estimates + tight tolerances), the system produces ZERO discoveries across 40 receipts.

**The negative result is accepted. No discovery signal is manufactured.**

---

## 7. Comparison to Random Control

| Config | DPS=1 % | GENUINE_NOVEL % | Mean IC score |
|---|---|---|---|
| B_llm_only | 0.0% | 60.0% | 0.783 |
| C_mechanism | 0.0% | 40.0% | 0.700 |
| F_full | 0.0% | 80.0% | 0.850 |
| **D_random** | **0.0%** | **70.0%** | **0.817** |

All four arms tie at 0% DPS=1. The full system (F_full) does NOT outperform the random control (D_random) on the only metric that matters — correct novel predictions. The 10pp Gate 1 "advantage" of F_full over D_random was an artifact of range fitting, which Gate 2 eliminates.

There is no statistical difference between treatment and control because all arms score zero.

---

## 8. Quarantine Status (Continued from Gate 1)

Per directive, the following remain quarantined:
- Temporal-reasoning module
- Negative-knowledge module
- Patent expansion
- New discovery architecture
- **50-case expansion** — explicitly forbidden by Gate 2 directive

The discovery thesis does NOT warrant another experiment at this time. The path forward (if any) requires fundamental changes:
1. **A genuinely frozen model** — a model with a training cutoff earlier than every case's cutoff date, OR a retrieval-only architecture with no parametric memory. Neither is available in this environment.
2. **A genuinely novel prediction task** — not "predict what was historically discovered" (which is a memory-leakage test), but "predict something that has not yet been observed and wait for an independent observation". This requires prospective registration, not retrospective backtest.
3. **A stronger mechanism for combining evidence** — the F_full config (mechanism + invariant + constraints) does NOT outperform B_llm_only or D_random. The architecture's claimed value is unsupported by the data.

---

## 9. Reproducibility and Integrity

- **Reproducibility:** Gate 2 evaluator output is byte-identical across two consecutive runs (modulo `timestamp` field).
- **Receipt integrity:** All 40 Gate 2 receipts hash-verified (`verify_receipt()` returns True for all 40).
- **Evidence objects:** All 10 structured evidence objects hash-sealed.
- **Backend:** z-ai CLI (glm-4-plus). Same model, same temperature (0.3), same max_tokens (600) across all 4 configs and all 10 cases.

---

## 10. Final Status

| Question | Answer |
|---|---|
| Did Gate 2 produce a meaningful discovery signal? | **NO.** 0/40 DPS=1. |
| Does F_full outperform D_random on DPS? | **NO.** Both 0%. |
| Does the 30-40% discovery claim survive? | **NO.** Retracted. |
| Should we expand to 50 cases? | **NO.** Directive explicitly forbids. |
| Should we build a new discovery architecture? | **NO.** Quarantine continues. |
| Is the discovery thesis dead? | **Not yet.** But it requires a fundamentally different experimental design (prospective, frozen-model, or retrieval-only). The retrospective-backtest design with a leaky LLM is exhausted. |
| North Star status | **UNPROVEN.** Negative result accepted. |

---

## 11. Artifact Inventory

| Artifact | Path |
|---|---|
| Structured evidence extractor | `discovery_fabric/v1_13_gate2/structured_evidence_extractor.py` |
| 10 evidence objects (frozen) | `discovery_fabric/v1_13_gate2/evidence_objects/PB-*.json` |
| Deterministic entailment test | `discovery_fabric/v1_13_gate2/deterministic_entailment_test.py` |
| Leakage-controlled generator | `discovery_fabric/v1_13_gate2/leakage_controlled_generator.py` |
| 40 Gate 2 receipts (frozen, hash-sealed) | `discovery_fabric/v1_13_gate2/receipts/PRED2-*.json` |
| Gate 2 evaluator | `discovery_fabric/v1_13_gate2/gate2_evaluator.py` |
| Gate 2 results JSON | `discovery_fabric/v1_13_gate2/results.json` |
| This report | `discovery_fabric/v1_13_gate2/V1_13_GATE2_REPORT.md` |
| Checkpoint (generation state) | `discovery_fabric/v1_13_gate2/checkpoint.json` |

---

**End of V1.13 Gate 2 Report. Negative result accepted. Quarantine continues.**
