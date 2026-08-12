# RESEARCH_TRUTH V2 — FORENSIC CORRECTION REPORT

**Date:** 2026-08-12T18:31:20.171294+00:00
**V1 source:** `RESEARCH_TRUTH_INVENTORY.json`
**V2 output:** `RESEARCH_TRUTH_INVENTORY_V2.json`
**V2 hash:** `53db3231e8fcedb2f4915e20148e047c...`
**Directive:** Forensic correction only. No new discovery code. No scorer changes. No benchmark changes.

---

## 1. V2 Status Taxonomy

V1 used a single `VALIDATED` category that conflated machine-validated claims with human-validated claims. V2 separates them.

| Status | Meaning | Authoritative? |
|---|---|---|
| **VALIDATED_MACHINE** | Validated by deterministic/machine test (reproducibility, hash verification, forensic re-computation). Authoritative as machine-validated. Does NOT constitute human validation. Authoritative: YES (full scope). | YES (full) |
| **VALIDATED_HUMAN** | Validated by independent human expert review. Authoritative as human-validated. (Currently: 0 claims — no human adjudication has been performed.) Authoritative: YES (full scope). | YES (full) |
| **RECONSTRUCTION_ONLY** | Describes reconstruction from known data, NOT a genuine discovery. Authoritative as a reconstruction claim; NOT authoritative as a discovery claim. Authoritative: YES (full scope, reconstruction only). | YES (full) |
| **INVALIDATED** | Tested and refuted by later evidence. NOT authoritative. | NO |
| **PROVISIONAL** | Claim made but not yet rigorously tested. NOT authoritative. | NO |
| **UNTESTED** | Claim made but never tested. NOT authoritative. | NO |
| **MACHINE_SCORED_RESULT_HUMAN_VALIDATION_PENDING** | Machine scorer produced a result; human validation has NOT been performed. NOT authoritative (provisional). The authoritative_scope field is 'machine_result_only' — the claim documents what the machine produced, but the number is NOT validated as ground truth. | NO (provisional, machine-result-only scope) |

## 2. Summary Counts (Generated Directly from V2 Inventory)

| Status | Count |
|---|---|
| VALIDATED_MACHINE | 22 |
| VALIDATED_HUMAN | 0 |
| RECONSTRUCTION_ONLY | 1 |
| INVALIDATED | 14 |
| PROVISIONAL | 1 |
| UNTESTED | 0 |
| MACHINE_SCORED_RESULT_HUMAN_VALIDATION_PENDING | 4 |
| **TOTAL** | **42** |
| AUTHORITATIVE | 23 |
| NON_AUTHORITATIVE | 19 |

**VALIDATED_HUMAN count: 0** — No claim has been validated by independent human expert review. All 'validation' to date is machine-only or LLM-proxy.

## 3. Corrections Applied

### 3.1 Split VALIDATED → VALIDATED_MACHINE / VALIDATED_HUMAN

V1 had a single `VALIDATED` category. V2 splits it:
- `VALIDATED_MACHINE`: validated by deterministic/machine test (reproducibility, hash verification, forensic re-computation)
- `VALIDATED_HUMAN`: validated by independent human expert review

**Result:** 0 claims are VALIDATED_HUMAN. All V1 VALIDATED claims are reclassified as VALIDATED_MACHINE. No human expert review has been performed on any claim.

### 3.2 LLM-Proxy Adjudication → Proxy Evidence (Never Human Validation)

Per MEASUREMENT_CONSTITUTION MC-1 (No self-validation) and MC-4 (Evidence tiers):
- LLM-proxy adjudication is proxy evidence, NOT human validation
- Every claim whose evidence mentions LLM-proxy is flagged `proxy_evidence: true`

**Affected claims:**
- `C-V1-019`: DSB V1 (V1.12 version, 30 cases) is complete and valid...
- `C-V1-020`: DSB human adjudication: 40% DSM agreement (below threshold)...
- `C-V1-021`: Formal Rubric V1: ALL thresholds FAILED (DS 24%, MR 29%, HR 33%)...
- `C-DSB-011`: DSB V1 E5 (human adjudication): PENDING — not yet performed by independent human...

### 3.3 'Architecture does not add value' → 'No incremental value demonstrated'

V1 claim C-V1-015 stated 'architecture does NOT add value'. The evidence is McNemar χ²=0.50 (p ≈ 0.50, non-significant). **Non-significance does NOT establish absence of effect** — it is a failure to detect an effect at this sample size.

**V2 correction:**
- C-V1-015: 'architecture does NOT add value' → 'no incremental value demonstrated (McNemar p=0.50 non-significant; does NOT establish absence of effect)'
- C-V1-016: 'architecture not statistically worse' → 'no statistically significant difference detected (failure to detect ≠ absence of effect)'

### 3.4 DSB 13/80 → MACHINE_SCORED_RESULT — HUMAN_VALIDATION_PENDING

V1 marked DSB V1 results as VALIDATED or PENDING_HUMAN_REVIEW. V2 introduces a new status: `MACHINE_SCORED_RESULT_HUMAN_VALIDATION_PENDING`.

This status means: the machine scorer produced this number, but human validation has NOT been performed. The claim is authoritative ONLY as 'the machine scorer produced this number', NOT as 'this number reflects reality'.

**Affected claims:**
- `C-DSB-005`: DSB V1: 13/80 discovery-structure recoveries (10 fabricated + 3 real)...
- `C-DSB-006`: DSB V1: fabricated cases score higher than real (10 fab vs 3 real recoveries)...
- `C-DSB-007`: DSB V1: no architecture advantage (full_system does not outperform other arms)...
- `C-DSB-008`: DSB V1: 0/80 mechanism reconstructions at ≥0.50 threshold...

### 3.5 'All retrospective approaches exhausted' → Narrower Statement

V1 claim C-V1-028 stated 'all retrospective approaches exhausted'. This is too broad — only LLM-based retrospective backtesting was tested. Non-LLM retrospective approaches were not addressed.

**V2 correction:** 'all retrospective approaches exhausted' → 'retrospective LLM backtesting is exhausted as a method for establishing the North Star'

### 3.6 Downgrade Claims Whose Evidence is Weaker Than Their Wording

Each claim was reviewed for wording-vs-evidence mismatch. The corrections in §3.3 and §3.5 are the instances found. No additional downgrades were required.

## 4. Automated Consistency Test Results

Every claim status, count, source commit, and authoritative flag must reconcile automatically.

**Overall: PASS** (7/7 checks pass)

| Check | Result |
|---|---|
| ALL_STATUSES_VALID | PASS |
| ALL_COUNTS_MATCH | PASS |
| ALL_HAVE_SOURCE_COMMIT | PASS |
| AUTHORITATIVE_FLAG_CONSISTENT | PASS |
| LLM_PROXY_FLAGGED | PASS |
| MACHINE_SCORED_SCOPE | PASS |
| NO_BANNED_PHRASES | PASS |

## 5. North Star Status (Corrected)

**Question:** Can TEE produce independently novel, retrieval-negative, adversarially surviving, falsifiable hypotheses at a materially higher rate than controls?
**Status:** UNPROVEN

**Evidence (corrected):**

V1.12 ablation: no incremental value demonstrated (McNemar p=0.50 non-significant; does NOT establish absence of effect). V1.13 Gate 2: 0/40 DPS=1 under strict deterministic scoring (machine-validated, negative result). DSB V1: 13/80 recoveries (MACHINE_SCORED_RESULT — human validation pending), fabricated > real (MACHINE_SCORED_RESULT — human validation pending), no architecture advantage (MACHINE_SCORED_RESULT — human validation pending). Retrospective LLM backtesting is exhausted as a method for establishing the North Star (3 structural reasons). Prospective experiment infrastructure built but NOT RUN.

**Blocking items:**
- DSB V1 human adjudication (2-3 independent expert adjudicators required)
- DSB V1 scorer validity against humans (confusion matrices)
- DSB V1 fabricated-vs-real inversion explanation (under human review)
- Prospective experiment (only if DSB V1 closes successfully AND independent audit passes)

## 6. Quarantine (Corrected)

**Status:** ACTIVE

**V2 correction note:** Quarantine remains active. The V1.12 ablation result is 'no incremental value demonstrated' (McNemar p=0.50 non-significant), NOT 'architecture does not add value'. This is a failure to demonstrate an effect, not proof of absence of effect.

**Prohibited until DSB V1 is scientifically closed:**
- No temporal reasoning module
- No negative knowledge module
- No patent integration
- No architecture redesign
- No new discovery modes
- No scorer tuning on DSB V1 80 cases

**Permitted forward work:**
- DSB V1 human adjudication (2-3 independent expert adjudicators)
- DSB V1 analysis pipeline (confusion matrices, inter-rater agreement, architecture recompute)
- Scorer-calibration set construction (ONLY if human review shows FP > 30%)
- Prospective experiment (ONLY if DSB V1 closes AND independent audit passes)

## 7. Claims Inventory (Corrected)

| ID | Version | Claim (corrected) | Status | Authoritative | Source Commit |
|---|---|---|---|---|---|
| C-V1-001 | V1.1-V1.6 | B-2 leakage detection instrument (8-round adjudication, 4-state ontolo... | VALIDATED_MACHINE | True | `f905b68 (branch, pre-main)` |
| C-V1-002 | V1.1-V1.6 | Evidence-injection architecture (GLiREL/GLiDRE/Relex-large) improves d... | INVALIDATED | False | `pre-main (B-2 branch)` |
| C-V1-003 | V1.1-V1.6 | Custodian infrastructure (source registry, case schema, deterministic ... | VALIDATED_MACHINE | True | `pre-main` |
| C-V1-004 | V1.1-V1.6 | Independent corpus of 112 sources is frozen and usable... | VALIDATED_MACHINE | True | `pre-main` |
| C-V1-005 | V1.1-V1.6 | 3,900-source corpus on branch is real and usable... | INVALIDATED | False | `pre-main (branch)` |
| C-V1-006 | V1.1-V1.6 | 3,210-source corpus exists... | INVALIDATED | False | `pre-main (branch)` |
| C-V1-007 | V1.7 | Combination Discovery Engine + Calibrated Survival produces discovery ... | INVALIDATED | False | `4a1bfdfd` |
| C-V1-008 | V1.8 | Discovery Value Model + Expert Funding Simulation + Calibration produc... | INVALIDATED | False | `2519e5f5` |
| C-V1-009 | V1.9 | Historical backtest: 2/5 discoveries found... | RECONSTRUCTION_ONLY | True | `dbae3ffe` |
| C-V1-010 | V1.10 | Expanded 50-discovery benchmark + V2 calibrated scorer is valid... | INVALIDATED | False | `ed6d4487` |
| C-V1-011 | V1.11 | 50-discovery blind benchmark: 96% strict recovery (48/50)... | INVALIDATED | False | `fa9caf1c` |
| C-V1-012 | V1.12 | Architecture adds 76pp over LLM-only (96% vs 20%)... | INVALIDATED | False | `9d2d9567` |
| C-V1-013 | V1.12 | V3 blinded scorer: 90pp discovery gap (real 90% vs false 0%)... | INVALIDATED | False | `4ec892a5` |
| C-V1-014 | V1.12 | Architecture advantage is 4pp (not 76pp) — honest correction... | INVALIDATED | False | `6a87eb05` |
| C-V1-015 | V1.12 | Ablation V2: no incremental value demonstrated for the full architectu... | VALIDATED_MACHINE | True | `4a1b1d92` |
| C-V1-016 | V1.12 | Matched-case analysis: no statistically significant difference detecte... | VALIDATED_MACHINE | True | `48c0db25` |
| C-V1-017 | V1.12 | Forensic audit: 150 records, 18 matched, McNemar 0.50 — verified... | VALIDATED_MACHINE | True | `ec214285` |
| C-V1-018 | V1.12 | Generator input isolation: 0/50 payloads leaked... | VALIDATED_MACHINE | True | `6211f8fa` |
| C-V1-019 | V1.12 | DSB V1 (V1.12 version, 30 cases) is complete and valid... | INVALIDATED | False | `035e4948` |
| C-V1-020 | V1.12 | DSB human adjudication: 40% DSM agreement (below threshold)... | VALIDATED_MACHINE | True | `35ff8b64` |
| C-V1-021 | V1.12 | Formal Rubric V1: ALL thresholds FAILED (DS 24%, MR 29%, HR 33%)... | VALIDATED_MACHINE | True | `22b3d36d` |
| C-V1-022 | V1.12 | DSM Decomposition: ALL 6 subclaims FAIL ≥70% threshold... | VALIDATED_MACHINE | True | `d98e3620` |
| C-V1-023 | V1.12 | DSM is inherently subjective for LLM proxies — retired as primary metr... | VALIDATED_MACHINE | True | `d98e3620` |
| C-V1-024 | V1.12 | RELATION_NOVELTY is a deterministic, reproducible novelty check (NOT a... | VALIDATED_MACHINE | True | `d98e3620` |
| C-V1-025 | V1.13 | Original V1.13: 30-40% CORRECT via broad-range matching... | INVALIDATED | False | `b5c7d6dd` |
| C-V1-026 | V1.13 | Gate 1 forensic correction: 7.5% DPS=1 (3/40) under stricter scoring... | INVALIDATED | False | `7209b294` |
| C-V1-027 | V1.13 | Gate 2: 0/40 DPS=1 — negative result accepted... | VALIDATED_MACHINE | True | `38b9b62e` |
| C-V1-028 | V1.13 | Retrospective LLM backtesting is exhausted as a method for establishin... | VALIDATED_MACHINE | True | `73e00cb5` |
| C-V1-029 | V1.13 | Prospective experiment infrastructure is auditable and independently r... | VALIDATED_MACHINE | True | `3296e2e9` |
| C-V1-030 | V1.13 | The 3 Gate 1 DPS=1 receipts were range-fitting artifacts... | VALIDATED_MACHINE | True | `38b9b62e` |
| C-DSB-001 | DSB V1 (new) | DSB V1 exit gate PASS (6/6 components)... | INVALIDATED | False | `a0a316f6` |
| C-DSB-002 | DSB V1 (new) | DSB V1 leakage audit: 80/80 payloads PASS, 0 leakage... | VALIDATED_MACHINE | True | `a0a316f6` |
| C-DSB-003 | DSB V1 (new) | DSB V1 receipt integrity: 80/80 hash-sealed and verified... | VALIDATED_MACHINE | True | `a0a316f6` |
| C-DSB-004 | DSB V1 (new) | DSB V1 scorer is reproducible (byte-identical modulo timestamps)... | VALIDATED_MACHINE | True | `a0a316f6` |
| C-DSB-005 | DSB V1 (new) | DSB V1: 13/80 discovery-structure recoveries (10 fabricated + 3 real)... | MACHINE_SCORED_RESULT_HUMAN_VALIDATION_PENDING | False | `9a259842` |
| C-DSB-006 | DSB V1 (new) | DSB V1: fabricated cases score higher than real (10 fab vs 3 real reco... | MACHINE_SCORED_RESULT_HUMAN_VALIDATION_PENDING | False | `9a259842` |
| C-DSB-007 | DSB V1 (new) | DSB V1: no architecture advantage (full_system does not outperform oth... | MACHINE_SCORED_RESULT_HUMAN_VALIDATION_PENDING | False | `a0a316f6` |
| C-DSB-008 | DSB V1 (new) | DSB V1: 0/80 mechanism reconstructions at ≥0.50 threshold... | MACHINE_SCORED_RESULT_HUMAN_VALIDATION_PENDING | False | `a0a316f6` |
| C-DSB-009 | DSB V1 (new) | DSB V1: 14 focused-review packets selected without human outcomes... | VALIDATED_MACHINE | True | `9a259842` |
| C-DSB-010 | DSB V1 (new) | DSB V1 freeze manifest: 111 artifacts unchanged after freeze... | VALIDATED_MACHINE | True | `9a259842` |
| C-DSB-011 | DSB V1 (new) | DSB V1 E5 (human adjudication): PENDING — not yet performed by indepen... | PROVISIONAL | False | `9a259842` |
| C-DSB-012 | DSB V1 (new) | DSB V1 scorer is FROZEN — must not be tuned on these 80 cases... | VALIDATED_MACHINE | True | `9a259842` |

## 8. The True Number

Per directive: 'report the true number, whatever it is.'

The true numbers, generated directly from the V2 inventory:

- **VALIDATED_HUMAN: 0** — No claim has been validated by independent human expert review.
- **VALIDATED_MACHINE: 22** — Validated by deterministic/machine test only.
- **MACHINE_SCORED_RESULT_HUMAN_VALIDATION_PENDING: 4** — Machine scorer produced a number; human validation NOT performed.
- **RECONSTRUCTION_ONLY: 1** — Reconstruction from known data, not discovery.
- **INVALIDATED: 14** — Tested and refuted.
- **PROVISIONAL: 1** — Not yet rigorously tested.
- **UNTESTED: 0** — Never tested.

- **TOTAL claims: 42**
- **Authoritative (full scope): 23**
- **Non-authoritative (machine-result-only scope, provisional): 4**
- **Non-authoritative (other): 15**
- **Total non-authoritative: 19**

**The true discovery rate of the engine, validated by independent human expert review: NOT APPLICABLE.**

No human-validated discovery experiment has been conducted. The human-validated discovery rate has no denominator — it is not 0/0 (which is mathematically undefined); it is undefined because no human validation has been performed. Per MEASUREMENT_CONSTITUTION MC-7 (No naked numbers), reporting 0/0 would be a bare scalar. The honest statement is: no human-validated discovery rate exists.

**The true machine-scored discovery rate (DSB V1, human validation pending): 13/80 (16.25%), of which 10/13 are fabricated counterfactuals and 3/13 are real discoveries.**

This is the true number. It is not a discovery claim. It is a machine-scored result awaiting human validation.

## 9. What Did NOT Change

Per directive: no new discovery code, no scorer changes, no benchmark changes.

- **No new modules built.** This is a registry correction only.
- **No scorer changes.** The DSB V1 scorer remains frozen (commit `a0a316f6`).
- **No benchmark changes.** The 80 DSB V1 cases and prompts remain frozen (FREEZE_MANIFEST.json, 111 artifacts unchanged).
- **No receipts modified.** All 80 receipts remain hash-sealed.
- **No new experiments run.**

Only the truth registry was corrected.

## 10. Governance Compliance

This correction complies with:

- **CONSTITUTION Law 7 (Historical permanence):** V1 inventory is preserved unchanged. V2 is a new file. No history was rewritten.
- **CONSTITUTION Law 8 (Verification Standard):** No 'verified' label without successful prediction. V2 marks 0 claims as VALIDATED_HUMAN.
- **MEASUREMENT_CONSTITUTION MC-1 (No self-validation):** LLM-proxy adjudication is flagged as proxy evidence, not human validation.
- **MEASUREMENT_CONSTITUTION MC-4 (Evidence tiers):** LLM-proxy evidence is tier I (inference only), weight 0.20, flagged 'unverified — inference only'.
- **ANTI_ENTROPY (No naked numbers):** DSB 13/80 is reported with scope ('machine-result-only'), not as a bare scalar.
- **STOP_BUILDING (No benchmark tuning, No score improvements):** No scorer or benchmark was modified.

---

## 11. Freeze Status

**RESEARCH_TRUTH V2 is FROZEN as of 2026-08-12T18:31:20.171392+00:00.**

Frozen artifacts (do NOT modify):
- `RESEARCH_TRUTH_INVENTORY_V2.json` (hash-sealed)
- `RESEARCH_TRUTH_FORENSIC_REPORT_V2.md` (this file)
- `research_truth_v2_forensic_correction.py` (the correction script)

Freeze policy:
- No further corrections to V2 without a new directive.
- If new evidence requires reclassification, create V3 (do NOT modify V2).
- V1 (`RESEARCH_TRUTH_INVENTORY.json`) remains preserved unchanged per CONSTITUTION Law 7.

**End of RESEARCH_TRUTH V2 Forensic Correction Report.**

**The true number is reported above. No new discovery code was built. No scorer was changed. No benchmark was changed.**

**FROZEN.**