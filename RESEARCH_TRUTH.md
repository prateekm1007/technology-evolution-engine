# RESEARCH_TRUTH

**Date:** 2026-08-12
**Source commit:** `3f89e0f5`
**Purpose:** Every historical claim from V1.1 onward, classified. Machine-readable inventory at `RESEARCH_TRUTH_INVENTORY.json`.
**Policy:** No new architecture until this truth inventory and DSB human adjudication are complete.

---

## Classification Legend

| Status | Meaning | Authoritative? |
|---|---|---|
| **VALIDATED** | Survived rigorous testing (forensic re-computation, reproducibility, human or deterministic validation) | YES |
| **INVALIDATED** | Tested and refuted by later evidence | NO |
| **RECONSTRUCTION_ONLY** | Describes reconstruction from known data, NOT a genuine discovery | YES (as reconstruction claim, NOT as discovery claim) |
| **UNTESTED** | Claim made but never rigorously tested | NO |
| **PENDING_HUMAN_REVIEW** | Awaits independent human adjudication | Provisional |

---

## Section 1: Claims by Version

### V1.1–V1.6 (pre-main, B-2 branch + custodian)

| ID | Claim | Status | Authoritative? |
|---|---|---|---|
| C-V1-001 | B-2 leakage detection instrument (8-round, 4-state, frozen) works | **VALIDATED** | YES |
| C-V1-002 | Evidence-injection architecture (GLiREL/GLiDRE/Relex) improves discovery | **INVALIDATED** | NO |
| C-V1-003 | Custodian infrastructure (registry, schema, sampler, builder) is sound | **VALIDATED** | YES |
| C-V1-004 | Independent corpus of 112 sources is frozen and usable | **VALIDATED** | YES |
| C-V1-005 | 3,900-source corpus on branch is real | **INVALIDATED** (MOCK DATA) | NO |
| C-V1-006 | 3,210-source corpus exists | **INVALIDATED** (NOT FOUND) | NO |

### V1.7 (commit `4a1bfdfd`)

| ID | Claim | Status | Authoritative? |
|---|---|---|---|
| C-V1-007 | Combination Discovery Engine + Calibrated Survival produces signal | **INVALIDATED** | NO |

### V1.8 (commit `2519e5f5`)

| ID | Claim | Status | Authoritative? |
|---|---|---|---|
| C-V1-008 | Discovery Value Model + Expert Funding + Calibration produces signal | **INVALIDATED** | NO |

### V1.9 (commit `dbae3ffe`)

| ID | Claim | Status | Authoritative? |
|---|---|---|---|
| C-V1-009 | Historical backtest: 2/5 discoveries found | **RECONSTRUCTION_ONLY** | YES (as reconstruction rate, not discovery rate) |

### V1.10 (commit `ed6d4487`)

| ID | Claim | Status | Authoritative? |
|---|---|---|---|
| C-V1-010 | Expanded 50-discovery benchmark + V2 calibrated scorer is valid | **INVALIDATED** | NO |

### V1.11 (commit `fa9caf1c`)

| ID | Claim | Status | Authoritative? |
|---|---|---|---|
| C-V1-011 | 50-discovery blind benchmark: 96% strict recovery (48/50) | **INVALIDATED** | NO |

### V1.12 (commits `9d2d9567` through `d98e3620`)

| ID | Claim | Status | Authoritative? |
|---|---|---|---|
| C-V1-012 | Architecture adds 76pp over LLM-only (96% vs 20%) | **INVALIDATED** | NO |
| C-V1-013 | V3 blinded scorer: 90pp discovery gap (real 90% vs false 0%) | **INVALIDATED** | NO |
| C-V1-014 | Architecture advantage is 4pp (not 76pp) — honest correction | **INVALIDATED** (further refuted by ablation V2) | NO |
| C-V1-015 | Ablation V2: architecture does NOT add value (C_mechanism 100% best, F_full 63% worst) | **VALIDATED** | YES |
| C-V1-016 | Matched-case analysis: architecture not statistically worse | **VALIDATED** | YES |
| C-V1-017 | Forensic audit: 150 records, 18 matched, McNemar 0.50 — verified | **VALIDATED** | YES |
| C-V1-018 | Generator input isolation: 0/50 payloads leaked | **VALIDATED** | YES |
| C-V1-019 | DSB V1 (V1.12 version, 30 cases) is complete and valid | **INVALIDATED** | NO |
| C-V1-020 | DSB human adjudication: 40% DSM agreement (below threshold) | **VALIDATED** (as LLM-proxy result, NOT human) | YES (with caveat) |
| C-V1-021 | Formal Rubric V1: ALL thresholds FAILED (DS 24%, MR 29%, HR 33%) | **VALIDATED** | YES |
| C-V1-022 | DSM Decomposition: ALL 6 subclaims FAIL ≥70% threshold | **VALIDATED** | YES |
| C-V1-023 | DSM is inherently subjective for LLM proxies — retired as primary metric | **VALIDATED** | YES |
| C-V1-024 | RELATION_NOVELTY is deterministic novelty check (NOT discovery metric) | **VALIDATED** | YES |

### V1.13 (commits `b5c7d6dd` through `3296e2e9`)

| ID | Claim | Status | Authoritative? |
|---|---|---|---|
| C-V1-025 | Original V1.13: 30-40% CORRECT via broad-range matching | **INVALIDATED** | NO |
| C-V1-026 | Gate 1 forensic correction: 7.5% DPS=1 (3/40) | **INVALIDATED** (range-fitting artifacts) | NO |
| C-V1-027 | Gate 2: 0/40 DPS=1 — negative result accepted | **VALIDATED** | YES |
| C-V1-028 | Retrospective LLM evaluation cannot establish the North Star | **VALIDATED** | YES |
| C-V1-029 | Prospective experiment infrastructure is auditable and independently reproducible | **VALIDATED** | YES |
| C-V1-030 | The 3 Gate 1 DPS=1 receipts were range-fitting artifacts | **VALIDATED** | YES |

### DSB V1 (new, commits `a0a316f6` through `3f89e0f5`)

| ID | Claim | Status | Authoritative? |
|---|---|---|---|
| C-DSB-001 | DSB V1 exit gate PASS (6/6 components) | **INVALIDATED** (relisted to PENDING) | NO |
| C-DSB-002 | Leakage audit: 80/80 payloads PASS, 0 leakage | **VALIDATED** | YES |
| C-DSB-003 | Receipt integrity: 80/80 hash-sealed and verified | **VALIDATED** | YES |
| C-DSB-004 | Scorer is reproducible (byte-identical modulo timestamps) | **VALIDATED** | YES |
| C-DSB-005 | 13/80 discovery-structure recoveries (10 fabricated + 3 real) | **VALIDATED** | YES |
| C-DSB-006 | Fabricated cases score higher than real (10 fab vs 3 real) | **PENDING_HUMAN_REVIEW** | Provisional |
| C-DSB-007 | No architecture advantage (full_system does not outperform other arms) | **PENDING_HUMAN_REVIEW** | Provisional |
| C-DSB-008 | 0/80 mechanism reconstructions at ≥0.50 threshold | **PENDING_HUMAN_REVIEW** | Provisional |
| C-DSB-009 | 14 focused-review packets selected without human outcomes | **VALIDATED** | YES |
| C-DSB-010 | Freeze manifest: 111 artifacts unchanged after freeze | **VALIDATED** | YES |
| C-DSB-011 | E5 (human adjudication): PENDING — not yet performed | **PENDING_HUMAN_REVIEW** | Provisional |
| C-DSB-012 | Scorer is FROZEN — must not be tuned on these 80 cases | **VALIDATED** | YES |

---

## Section 2: Summary Counts

| Status | Count |
|---|---|
| VALIDATED | 23 |
| INVALIDATED | 14 |
| RECONSTRUCTION_ONLY | 1 |
| UNTESTED | 0 |
| PENDING_HUMAN_REVIEW | 4 |
| **Total** | **42** |

- Authoritative claims: 28
- Non-authoritative claims: 14
- Modules inventoried: 13
- Scorers inventoried: 6
- Benchmarks inventoried: 7
- Reports inventoried: 18
- Commits mapped: 28

---

## Section 3: North Star Status

**Question:** Can TEE produce independently novel, retrieval-negative, adversarially surviving, falsifiable hypotheses at a materially higher rate than controls?

**Status: UNPROVEN**

**Authoritative evidence:**
1. V1.12 ablation (C-V1-015): architecture does NOT add value; McNemar χ²=0.50 (not significant)
2. V1.13 Gate 2 (C-V1-027): 0/40 DPS=1 under strict deterministic scoring
3. DSB V1 (C-DSB-005, C-DSB-006, C-DSB-007): 13/80 recoveries, fabricated > real, no architecture advantage
4. Retrospective evaluation exhausted (C-V1-028): 3 structural reasons retrospective LLM evaluation cannot establish the North Star

**Blocking items (in order):**
1. DSB V1 human adjudication (2-3 independent expert adjudicators)
2. DSB V1 scorer validity against humans (confusion matrices)
3. DSB V1 fabricated-vs-real inversion explanation
4. (Conditional) Prospective experiment

---

## Section 4: Quarantine

**Status: ACTIVE**

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

---

## Section 5: The Excellent Failure (per directive)

The engine, forced into a benchmark where the answer relationship is withheld (DSB V1), produced:
- 0/80 mechanism reconstructions
- 13/80 discovery-structure recoveries (16.25%)
- 10 fabricated recoveries vs 3 real recoveries (fabricated scores 3.3× higher)
- No architecture advantage

This is the productive negative result. The engine is not yet discovering anything — and it has been forced into a benchmark that proves it. That is exactly the kind of failure a world-class discovery engine needs to expose before we trust it.

---

## Section 6: Machine-Readable Inventory

The full machine-readable inventory is at `RESEARCH_TRUTH_INVENTORY.json`. It contains:
- 28 commits with dates and subjects
- 41 claims with version, source commit, status, authoritative flag, evidence, notes
- 13 modules with path, source commit, authoritative flag, status, notes
- 6 scorers with version, source commit, authoritative flag, status, notes
- 7 benchmarks with version, source commit, authoritative flag, status, notes
- 18 reports with path, source commit, authoritative flag, status, notes
- North Star status + blocking items
- Quarantine status + permitted/prohibited work

---

**End of RESEARCH_TRUTH. No new architecture until this inventory and DSB human adjudication are complete.**
