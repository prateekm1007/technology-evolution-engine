# EXPERT_SPECIFICATION — Arm F (Expert Baseline)

**Status:** FROZEN — immutable expert control specification
**Date:** 2026-08-10
**Purpose:** The expert baseline is a real scientific instrument, not "find someone smart and ask them."

---

## The Expert Question

> **Can a qualified human expert, given the same two source documents and a controlled information budget, produce the same candidates that TEE produces?**

---

## Immutable Parameters

| # | Parameter | Value | Notes |
|---|-----------|-------|-------|
| 1 | Number of experts | 3 (minimum for inter-rater reliability) | Single expert creates unacceptable variance. |
| 2 | Domain qualification | PhD or equivalent in a relevant scientific field, OR 5+ years published research experience | Must be relevant to at least one of the benchmark domains. |
| 3 | Selection procedure | Independent recruitment by custodian. Experts must NOT be affiliated with the TEE project. | No COI with the system being tested. |
| 4 | Conflict-of-interest rules | Experts must disclose: prior knowledge of TEE, prior work on the benchmark cases, financial interest in outcomes. Any COI → exclusion. | Enforced by custodian. |
| 5 | Information available | Source document A + Source document B + candidate problem prompt (identical to C2) | Same information budget as all other arms. |
| 6 | External browsing | PROHIBITED | No internet access during the task. |
| 7 | External literature access | PROHIBITED | No looking up papers, textbooks, or reference material. |
| 8 | Calculator/code access | PERMITTED (basic calculator only; no LLM access, no simulation tools) | Leveling the playing field — TEE cannot do complex math either. |
| 9 | Collaboration | PROHIBITED | Each expert works independently. No discussion between experts. |
| 10 | Time budget | 30 minutes per case | Generous for a qualified expert. Not a bottleneck. |
| 11 | Output format | Same schema as TEE (b2-trace-v3 JSON) | For fair comparison. Experts given a form/template to fill. |
| 12 | Scoring rubric | Same as all arms: mechanism correctness, causal variable, direction, magnitude, falsifiability | Frozen rubric. No post-hoc changes. |
| 13 | Adjudication | Blind scoring by independent evaluator (not the experts themselves) | Evaluator does not know which arm produced which output. |
| 14 | Compensation | $100 per case (competitive for expert time) | Incentivizes effort without creating outcome bias. |
| 15 | Blinding | Experts are blind to: which system is TEE, the ground truth, the expected answer, and other experts' outputs | Enforced by custodian. |

---

## Expert Protocol

### Step 1: Recruitment (Custodian)
- Custodian recruits 3+ experts per domain (or per case cluster)
- Experts sign COI disclosure
- Experts agree to information-budget rules (no internet, no literature, no collaboration)

### Step 2: Task Administration (Custodian)
- Expert receives: Source A, Source B, candidate problem prompt, output template
- Expert has 30 minutes
- Expert is monitored (screen recording or proctored session) to enforce information budget
- Expert submits JSON-formatted output

### Step 3: Scoring (Independent Evaluator)
- All expert outputs are pooled with TEE, C2, retrieval, and null outputs
- Evaluator scores ALL outputs blind (does not know which arm produced which)
- Scoring rubric is the frozen rubric (mechanism, variable, direction, magnitude, falsifier)

### Step 4: Inter-Rater Reliability
- If 3 experts disagree on a case, majority vote determines the expert-arm label
- Inter-rater agreement (Cohen's κ or Krippendorff's α) is reported
- If κ < 0.4, the expert arm is reported as unreliable for that case

---

## What Expert Tests

| If expert result | Interpretation |
|-----------------|---------------|
| Expert ≈ TEE | TEE adds no value over a qualified human. |
| Expert < TEE | TEE outperforms humans. (Surprising and significant.) |
| Expert > TEE | TEE is worse than human reasoning. (Architecture is insufficient.) |

---

## Adversarial Gate

Expert output is run through the **SAME unchanged adversarial gate** as TEE. No special treatment. The gate does not know the output came from a human.

---

## Freeze Status

**FROZEN.** All 15 parameters are immutable.

---

## Preflight Checklist Update

| Item | Status Before | Status After |
|------|--------------|-------------|
| 6. Expert protocol (Arm F) frozen | ⬜ NOT FROZEN | ✅ PASS |
