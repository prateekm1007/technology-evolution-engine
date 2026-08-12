# DSB V1 — Discovery-Structure Benchmark V1 Report (UPDATED)

**Date:** 2026-08-12 (updated per directive "V1 DSB IS NOT SCIENTIFICALLY CLOSED")
**Task ID:** dsb-v1-not-closed-human-adjudication-pending
**Status:** NOT SCIENTIFICALLY CLOSED. E5 relabeled PENDING_HUMAN_ADJUDICATION. Artifacts FROZEN. Awaiting 2-3 independent expert adjudicators.
**Scope:** DSB V1 only. No temporal reasoning, no negative knowledge, no patents, no additional discovery modes, no architecture redesign.

---

## 0. The Most Important Finding (per directive)

> "The engine is not yet discovering anything. It has now been forced into a benchmark where the answer relationship is withheld, and its performance collapsed to 15%, with fabricated ideas doing better than real ones. That is exactly the kind of failure a world-class discovery engine needs to expose before we trust it."

This is the correct framing. The DSB V1 result is a **productive negative result** — it exposes that the engine, under properly controlled conditions (answer withheld, leakage audited, fabricated counterfactuals present), does NOT discover at a meaningful rate and is biased toward plausible-sounding fabrications. This is exactly the kind of failure that must be exposed before any discovery claim can be trusted.

---

## 1. What Changed in This Update (per directive)

1. **E5 relabeled:** `E5_HUMAN_ADJUDICATION` is now `PENDING_HUMAN_ADJUDICATION`, not `PASS`. The exit gate now reports `NOT CLOSED` instead of `PASS`.
2. **Artifacts FROZEN:** 111 artifacts hash-sealed in `FREEZE_MANIFEST.json`. The 80 cases and prompts are NOT modified. The scorer is NOT tuned.
3. **Adjudication infrastructure built:** Adjudicator instructions, results template, focused review packet (14 priority packets), confusion-matrix module, inter-rater-agreement module, architecture-recompute module (FROZEN until human results arrive).
4. **Scorer-calibration protocol defined:** If human adjudication reveals systematic false positives, a SEPARATE calibration set (40 new cases) will be built. The DSB V1 scorer is NOT tuned on the DSB V1 80 cases.
5. **Recovery count corrected:** Earlier report said 12/80 (15%); actual count is 13/80 (16.25%) — 10 fabricated + 3 real.
6. **Quarantine continued:** No temporal reasoning, no negative knowledge, no patents, no architecture redesign until DSB V1 is scientifically closed.

---

## 2. Frozen Artifacts

111 artifacts are hash-sealed in `discovery_fabric/dsb_v1/FREEZE_MANIFEST.json`:

- 10 real cases (`cases/real/DSB-R-*.json`)
- 10 fabricated cases (`cases/fabricated/DSB-F-*.json`)
- 80 receipts (`receipts/RECEIPT-*.json`)
- 10 module source files (`case_schema.py`, `build_real_cases.py`, `build_fabricated_cases.py`, `payload_builder.py`, `leakage_audit.py`, `generator.py`, `scorer.py`, `human_adjudication_packet.py`, `recomputation_check.py`, `run_dsb_v1.py`)
- 1 blind adjudication packet file (`adjudication/adjudication_packets_BLIND.json`)

The freeze manifest is itself hash-sealed. Any modification to any frozen artifact is detectable by re-running `python3 freeze_manifest.py` and diffing the hashes.

---

## 3. Exit Gate Status (UPDATED)

| Gate | Status | Details |
|---|---|---|
| E1_LEAKAGE_AUDIT | **PASS** | 80/80 payloads pass L1-L7 |
| E2_PAYLOAD_HASHES | **PASS** | 80/80 payload hashes verified |
| E3_SCORER_VALIDATION | **PASS** | Scorer reproducible (byte-identical modulo timestamps) |
| E4_CONTROLS | **PASS** | 4 arms × 20 cases = 80 receipts, all hash-sealed |
| E5_HUMAN_ADJUDICATION | **PENDING_HUMAN_ADJUDICATION** | Packets built (80/80) but adjudication NOT performed. Requires 2-3 independent expert adjudicators. |
| E6_REPRODUCIBLE_RECOMPUTATION | **PASS** | 5/5 recomputation checks pass |

**EXIT GATE: NOT CLOSED** (1 gate PENDING human adjudication)

**DSB V1 SCIENTIFICALLY CLOSED: NO**

---

## 4. What Is Required to Close DSB V1

Per the directive, DSB V1 is complete ONLY when ALL of the following are done:

### 4.1 Human adjudication (E5)
- 2-3 independent expert adjudicators score all 80 blind packets
- Adjudicators must NOT be the experimenter or an LLM proxy
- Adjudicators answer Q1 (MECHANISM_MATCH), Q2 (DISCOVERY_STRUCTURE_MATCH), Q3 (SPECIFICITY) per packet
- Adjudicators sign an independence statement

### 4.2 Inter-rater agreement
- Cohen's kappa (for 2 raters) or Fleiss' kappa (for 3+ raters) per question
- Target: κ ≥ 0.40 (moderate agreement) for Q2 (the primary discovery-structure question)
- If κ < 0.40, the adjudicator protocol needs revision before proceeding

### 4.3 Human vs deterministic-scorer confusion matrices
- Computed separately for real and fabricated cases
- Both strict (human YES = positive) and lenient (human YES/PARTIAL = positive) modes
- Key metric: false-positive rate on fabricated cases
- If FP rate on fabricated > 30%, the scorer has systematic false positives → trigger scorer-calibration protocol

### 4.4 Focused review of the 13 machine "recoveries"
- 14 priority packets extracted to `adjudication/focused_review_packets_BLIND.json`
- Includes all 13 RECOVERED cases + top-2 fabricated per arm
- Adjudicators do NOT know which packets are in this subset or why
- Adjudicators should pay extra attention to these packets

### 4.5 Adjudicator-blind review of fabricated > real cases
- Part of the focused review (§4.4)
- Question: do humans also rate fabricated > real, or only the deterministic scorer?

### 4.6 Explain the fabricated-vs-real inversion
- Three possible explanations:
  - (a) Scorer too lenient on plausible-sounding combinations → humans will NOT show the inversion
  - (b) LLM better at inventing than recovering → humans WILL show the inversion
  - (c) Case design flaw (fabricated cases are "easier") → humans WILL show the inversion, but case audit is needed
- The explanation determines the next step:
  - If (a): trigger scorer-calibration protocol
  - If (b): the LLM has a fundamental discovery failure — no architecture redesign helps
  - If (c): rebuild the case set with stricter fabricated-case controls

### 4.7 Recompute architecture comparison
- Run `architecture_recompute.py` (currently FROZEN) after human results arrive
- Compare arm performance under human gold standard
- If no arm outperforms others under human judgment, the architecture-comparison question is settled (negatively)

---

## 5. Scorer-Calibration Protocol (if needed)

If human adjudication reveals systematic false positives (FP rate on fabricated > 30%), a SEPARATE scorer-calibration set will be built:

- 40 new cases (20 real + 20 fabricated), NOT overlapping with DSB V1's 20
- Same case schema
- Human-adjudicated independently
- Scorer v2 tuned on calibration set, then evaluated ONE-SHOT on DSB V1 80 cases
- Both v1 (frozen) and v2 (calibrated) results reported

The DSB V1 scorer is NOT tuned on the DSB V1 80 cases. Full protocol in `SCORER_CALIBRATION_PROTOCOL.md`.

---

## 6. Scorer Results (FROZEN — deterministic, 80 receipts)

These results are FROZEN at commit `a0a316f6`. They will NOT be recomputed unless the scorer is replaced (per §5).

### 6.1 Two outcomes scored

**Outcome 1: MECHANISM_RECONSTRUCTION**
- Compares `proposed.mechanism` with `case.answer_mechanism`
- Score = content-term overlap ratio (overlap coefficient)
- Verdict: RECONSTRUCTED if score ≥ 0.50, else NOT_RECONSTRUCTED

**Outcome 2: DISCOVERY_STRUCTURE_RECOVERY**
- Three sub-scores:
  - (a) ENTITY_OVERLAP (weight 0.5): content-term overlap between proposed_relationship and breakthrough_relationship
  - (b) RELATION_TYPE_MATCH (weight 0.25): do both express the same relation type?
  - (c) NOVEL_RELATION (weight 0.25): does proposed introduce terms/relation types NOT in exposed_facts?
- Final score = 0.5(a) + 0.25(b) + 0.25(c)
- Verdict: RECOVERED if score ≥ 0.50 AND novelty ≥ 0.30

### 6.2 Results by arm × case_type (FROZEN)

| Arm | Type | N | MechR | DiscR | MechAvg | DiscAvg |
|---|---|---|---|---|---|---|
| LLM_only | fabricated | 10 | 0 | 3 | 0.196 | 0.374 |
| LLM_only | real | 10 | 0 | 0 | 0.253 | 0.291 |
| mechanism_only | fabricated | 10 | 0 | 1 | 0.126 | 0.293 |
| mechanism_only | real | 10 | 0 | 1 | 0.145 | 0.306 |
| combination | fabricated | 10 | 0 | 4 | 0.193 | 0.401 |
| combination | real | 10 | 0 | 2 | 0.214 | 0.311 |
| full_system | fabricated | 10 | 0 | 2 | 0.230 | 0.385 |
| full_system | real | 10 | 0 | 0 | 0.237 | 0.313 |

### 6.3 The 13 recoveries (corrected from earlier "12")

| Receipt | Case Type | Arm | Score |
|---|---|---|---|
| DSB-F-001-LLM_only | fabricated | LLM_only | 0.5536 |
| DSB-F-001-combination | fabricated | combination | 0.5784 |
| DSB-F-005-LLM_only | fabricated | LLM_only | 0.6705 |
| DSB-F-005-combination | fabricated | combination | 0.5278 |
| DSB-F-005-full_system | fabricated | full_system | 0.6705 |
| DSB-F-006-LLM_only | fabricated | LLM_only | 0.5521 |
| DSB-F-006-combination | fabricated | combination | 0.5833 |
| DSB-F-006-mechanism_only | fabricated | mechanism_only | 0.6167 |
| DSB-F-007-combination | fabricated | combination | 0.5122 |
| DSB-F-010-full_system | fabricated | full_system | 0.5607 |
| DSB-R-001-combination | real | combination | 0.6205 |
| DSB-R-007-combination | real | combination | 0.5486 |
| DSB-R-007-mechanism_only | real | mechanism_only | 0.5250 |

**10 fabricated + 3 real = 13 total recoveries (16.25%).**

The fabricated-vs-real inversion: 10/40 (25%) fabricated recoveries vs 3/40 (7.5%) real recoveries. **Fabricated cases score 3.3× higher than real cases.** This is the inversion that human adjudication must explain.

### 6.4 Honest interpretation (UNCHANGED from initial report)

1. **No architecture advantage.** full_system does NOT outperform other arms on either outcome.
2. **Fabricated > real.** The scorer gives fabricated counterfactuals higher discovery-structure scores than real discoveries. This may be (a) scorer too lenient, (b) LLM better at inventing than recovering, or (c) case design flaw. Human adjudication will distinguish.
3. **The engine is not discovering.** Under properly controlled conditions (answer withheld, leakage audited, fabricated counterfactuals present), the engine's discovery-structure recovery rate is 16.25%, with most "recoveries" being fabricated. This is the productive negative result the directive highlights.

---

## 7. What This Module Does NOT Do (per directive, continued)

- ❌ No temporal reasoning module
- ❌ No negative knowledge module
- ❌ No patent integration
- ❌ No additional discovery modes
- ❌ No architecture redesign
- ❌ No scorer tuning on these 80 cases
- ❌ No modification to the 80 cases or prompts

---

## 8. Adjudication Infrastructure (Built, Awaiting Humans)

| Artifact | Path | Status |
|---|---|---|
| Adjudicator instructions | `adjudication/instructions/ADJUDICATOR_INSTRUCTIONS.md` | Ready |
| Results template | `adjudication/instructions/adjudication_results_template.json` | Ready (80 packet slots) |
| Full blind packets (80) | `adjudication/adjudication_packets_BLIND.json` | Ready |
| Focused review packets (14) | `adjudication/focused_review_packets_BLIND.json` | Ready |
| Confusion-matrix module | `adjudication/analysis/confusion_matrix.py` | FROZEN (awaits results) |
| Inter-rater-agreement module | `adjudication/analysis/inter_rater_agreement.py` | FROZEN (awaits results) |
| Architecture-recompute module | `adjudication/analysis/architecture_recompute.py` | FROZEN (awaits results) |

---

## 9. How to Run the Human Adjudication Step

1. Recruit 2-3 independent expert adjudicators (domain experts in materials science, molecular biology, ML, immunology, or related fields). They must NOT be the experimenter or an LLM proxy.

2. Send each adjudicator:
   - `adjudication/instructions/ADJUDICATOR_INSTRUCTIONS.md`
   - `adjudication/instructions/adjudication_results_template.json`
   - `adjudication/adjudication_packets_BLIND.json`
   - `adjudication/focused_review_packets_BLIND.json` (14-packet subset for priority review)

3. Each adjudicator independently scores all 80 packets (Q1, Q2, Q3) and signs the independence statement. Estimated time: 2-4 hours per adjudicator.

4. Collect results as `adjudication/results/adjudicator_[ID].json` (one file per adjudicator).

5. Run the analysis pipeline:
   ```bash
   python3 discovery_fabric/dsb_v1/adjudication/analysis/inter_rater_agreement.py
   python3 discovery_fabric/dsb_v1/adjudication/analysis/confusion_matrix.py
   python3 discovery_fabric/dsb_v1/adjudication/analysis/architecture_recompute.py
   ```

6. Evaluate the exit criterion (§4). DSB V1 is closed ONLY when all 7 requirements (§4.1-§4.7) are met.

---

## 10. Quarantine (Continued)

Until DSB V1 is scientifically closed:

- ❌ No temporal reasoning module
- ❌ No negative knowledge module
- ❌ No patent integration
- ❌ No architecture redesign
- ❌ No new discovery modes
- ❌ No scorer tuning on DSB V1 80 cases

The ONLY permitted forward work is:
- ✅ Human adjudication of the 80 DSB V1 packets
- ✅ Analysis pipeline (confusion matrices, inter-rater agreement, architecture recompute)
- ✅ Scorer-calibration set construction (IF and ONLY IF human adjudication reveals systematic false positives)

---

**End of DSB V1 Report (Updated). DSB V1 is NOT scientifically closed. Awaiting human adjudication.**
