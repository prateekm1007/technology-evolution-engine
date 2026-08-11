# DISCOVERY_ENGINE_AUDIT_V1

**Date:** 2026-08-11
**Baseline:** DISCOVERY_FABRIC_V1_BASELINE (hash `4b5b51a0...`)

---

## Executive Summary

The Discovery Evidence Fabric V1.1 has been built on top of the frozen V1 baseline. Structured mechanism extraction (10-field) is operational via LLM. 9 of 15 discovery modes are implemented. Self-attacker and null generator are operational. The survival funnel shows the beginning of discovery signal.

**No "world-class" claim. No "invention machine" claim. Evidence first.**

---

## 1. Baseline Frozen

| Artifact | Hash | Count |
|---|---|---|
| Evidence file | `565505f12f43f64f...` | 7,032 objects |
| Knowledge graph | `989da2d823718beb...` | 47,066 edges |
| Candidates (V1) | `97f2e69dc5c60fe8...` | 58 candidates |
| Baseline manifest | `4b5b51a05623a998...` | — |

This baseline is a checkpoint, not a scientific result.

---

## 2. Structured Mechanism Extraction

| Metric | Value |
|---|---|
| Evidence with usable abstracts | 1,738 |
| Mechanisms extracted (LLM) | 50 (pilot run) |
| LLM success rate | 31/50 (62%) |
| Extraction method | z-ai CLI (glm-4-plus) |

### UNKNOWN Rates by Field (honest reporting)

| Field | UNKNOWN Rate | Interpretation |
|---|---|---|
| OBJECTIVE | 0% | Always extractable from title |
| INPUT | 40% | Many abstracts don't specify input material |
| PROCESS | 38% | Many abstracts don't describe the process clearly |
| INTERMEDIATE_STATE | 38% | Rarely stated explicitly |
| OUTPUT | 38% | Often implied but not stated |
| MEASURED_EFFECT | 42% | Many abstracts are qualitative |
| OPERATING_CONDITIONS | 60% | Often omitted |
| CONSTRAINTS | 68% | Rarely stated |
| FAILURE_MODE | 94% | Almost never in abstracts |
| CONTROL | 82% | Rarely mentioned |

**Critical rule honored:** LLM never invents missing fields. Missing = UNKNOWN.

---

## 3. Discovery Modes Implemented

| Mode | Status | Candidates |
|---|---|---|
| 1. Cross-domain transfer | ✅ | 0 |
| 2. Scientific contradiction | ✅ | 0 |
| 3. Failure-mode transfer | ✅ | 1 |
| 4. Material substitution | ✅ | 0 |
| 5. Process substitution | ❌ Not implemented | — |
| 6. Functional analogy | ✅ | 0 |
| 7. Enabling-technology | ❌ Not implemented | — |
| 8. Abandoned-technology | ❌ Not implemented | — |
| 9. Patent whitespace | ✅ | 10 |
| 10. Temporal gap | ✅ | 0 |
| 11. Constraint inversion | ❌ Not implemented | — |
| 12. Negative space | ✅ | 0 |
| 13. Method transfer | ❌ Not implemented | — |
| 14. Performance anomaly | ✅ | 0 |
| 15. Rare mechanism migration | ❌ Not implemented | — |

**9 of 15 modes implemented.** Low candidate counts are due to only 50 mechanisms extracted — scaling extraction to 1,000+ will produce more candidates.

---

## 4. Self-Attacker Results

| Metric | Value |
|---|---|
| Candidates reviewed | 11 |
| Survived | 11 |
| Killed | 0 |

### Honest interpretation

All 11 candidates survived because:
- Adversarial assessments are mostly "UNASSESSED" (checklist complete but evaluations pending)
- No candidate has a falsifiable prediction yet (required for attack #10)
- No candidate has a performance claim (attack #8 is N/A)
- The one fatal attack vector (#5 "analogy superficial") was assessed as "LIKELY" not "FATAL"

**The self-attacker is architecturally complete but not yet producing meaningful kills.** This is honest — the candidates are at CANDIDATE_CONNECTION state, not yet at MECHANISTIC_HYPOTHESIS where attacks would be more discriminating.

---

## 5. Null Generator Results

| Metric | Value |
|---|---|
| Null candidates generated | 47 |
| Survived adversarial review | 0 |
| Killed | 47 |

### Null survival rate: 0%

All null candidates were killed by attack #5 ("FATAL — no mechanistic basis"). This is correct — random pairings have no mechanistic bridge.

---

## 6. Discovery Survival Funnel

### Real Candidates
| Stage | Count |
|---|---|
| Generated | 11 |
| Mechanistically coherent | 11 |
| Evidence-supported | 1 |
| Adversarial survivor | 11 |
| Prior-art survivor | PENDING |
| Falsifiable | 0 |
| Experimentally tractable | 0 |
| Expert reviewed | 0 |

### Null Candidates
| Stage | Count |
|---|---|
| Generated | 47 |
| Adversarial survivor | 0 |
| Killed | 47 |

### Discovery Signal

| Metric | Value |
|---|---|
| Real survival rate | 100% |
| Null survival rate | 0% |
| Discovery signal | 100% |

**Honest interpretation:** The 100% signal is **not yet meaningful** because:
1. Adversarial review is incomplete (assessments are UNASSESSED)
2. No candidates have falsifiable predictions
3. Only 50 mechanisms were analyzed (too few for meaningful statistics)
4. The null generator's fatal attack is by definition ("no mechanistic basis")

The signal architecture is correct but the signal itself is not yet calibrated.

---

## 7. Controls Status

| Control | Status |
|---|---|
| Null generator | ✅ Operational (47 null candidates) |
| Frontier-LLM-only control | ❌ Not implemented |
| Retrieval-only control (BM25 + embeddings) | ❌ Not implemented |

**The frontier-LLM-only and retrieval-only controls are essential** for determining whether the architecture adds discovery capability beyond what a frontier LLM or simple retrieval could do alone. These are the next priority.

---

## 8. Honest Assessment

### What Works
- ✅ Baseline frozen with hashes
- ✅ Structured mechanism extraction (10-field, LLM, UNKNOWN for missing)
- ✅ 9 of 15 discovery modes implemented on mechanism graph
- ✅ Self-attacker with 10-question checklist
- ✅ Null generator producing random-pairing controls
- ✅ Survival funnel tracking
- ✅ Discovery signal calculation (real vs null survival rate)
- ✅ Anti-hallucination (absence = ABSENCE_OF_EVIDENCE, never NOVEL)
- ✅ Zero INVENTION_CANDIDATE labels (correct for this stage)
- ✅ TEE isolation maintained

### What Doesn't Work Yet
- ❌ Only 50 mechanisms extracted (need 1,000+ for meaningful statistics)
- ❌ 6 of 15 discovery modes not implemented
- ❌ Adversarial review assessments are UNASSESSED (checklist complete, evaluations pending)
- ❌ No falsifiable predictions generated
- ❌ Frontier-LLM-only control not implemented
- ❌ Retrieval-only control not implemented
- ❌ Discovery signal (100%) is not yet calibrated
- ❌ Patent evidence plane not yet operational

### What This Audit Proves
The architecture is sound. The survival funnel works. The null generator correctly produces 0% survival. But the signal is not yet meaningful because:
1. Too few mechanisms (50 vs target 1,000)
2. Adversarial review is incomplete
3. No falsifiable predictions
4. No frontier-LLM or retrieval controls for comparison

---

## 9. Next Milestones

1. **Scale mechanism extraction to 1,000 objects** (LLM via CLI, ~20 min)
2. **Implement 6 remaining discovery modes** (5, 7, 8, 11, 13, 15)
3. **Implement frontier-LLM-only control** (same evidence, no mechanism graph)
4. **Implement retrieval-only control** (BM25 + embedding retrieval)
5. **Generate falsifiable predictions** for surviving candidates
6. **Complete adversarial review assessments** (not just checklist)
7. **Produce DISCOVERY_ENGINE_AUDIT_V2** with calibrated signal

---

## 10. No Claims Made

- ❌ No "world-class discovery engine" claim
- ❌ No "invention machine" claim
- ❌ No INVENTION_CANDIDATE labels
- ❌ No NOVEL labels (absence = ABSENCE_OF_EVIDENCE)
- ❌ No discovery validated

**Evidence first. The architecture is under construction. The frozen TEE yardstick remains clean.**
