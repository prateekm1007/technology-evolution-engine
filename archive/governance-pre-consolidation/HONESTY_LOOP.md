# HONESTY_LOOP

**Status:** Active governance loop. The 7th governance layer.
**Location:** repo root.
**Phase:** Post-BP-2 / Honesty Loop v1.0.
**Triggered by:** Consolidated external + internal review (CEO directive,
post-BP-2). The review found that the Blueprint produced "85.7% PASS"
verdicts, "58% confidence" labels, and "complete engineering blueprint"
claims — none of which the system has earned the right to make.

> The most important improvement is not the battery design itself.
> The most important improvement is that the system destroyed its
> own mistakes.
>
> A weather forecast can say "58% probability of rain" because it
> has decades of data, repeated observations, calibration curves,
> and millions of validation samples. Your system has none of
> those things. So "confidence = 58%" should disappear.
>
> Gate score is not engineering truth.
> — Consolidated review, post-BP-2

This document defines the loop that makes honesty mechanical — not
a virtue, not a slogan, not a "best effort." The loop reads the
governance files, scans every artifact, detects forbidden language,
requires typed replacements, and refuses to close until the
replacements land. It is the 7th governance layer:

| # | Layer | Document |
|---|---|---|
| 1 | Research process | CONSTITUTION.md |
| 2 | Documentation | EVIDENCE_STANDARDS.md |
| 3 | Architecture | REACHABILITY_CONSTITUTION.md |
| 4 | Product | BLUEPRINT_CONSTITUTION.md + ENGINEERING_PRINCIPLES.md |
| 5 | Coder directions | CODER_DIRECTIONS.md |
| 6 | Development pipeline | AEP_PROTOCOL.md |
| 7 | **Honesty loop** | **HONESTY_LOOP.md (this document)** |

The Honesty Loop sits ABOVE the AEP pipeline. Every artifact that
passes Gate 10 (Postmortem) of the AEP must then pass the Honesty
Loop's own gate (Gate 11 — Loop Closure) before it is shipped.

---

## The loop, drawn

```
            ┌─────────────────────────────────────────┐
            │  1. READ governance + anti-entropy      │
            │     (CONSTITUTION, ANTI_ENTROPY,        │
            │      BLUEPRINT_CONSTITUTION, AEP,       │
            │      ENGINEERING_PRINCIPLES, CODER_,    │
            │      HONESTY_LOOP)                      │
            └────────────────────┬────────────────────┘
                                 │
                                 ▼
            ┌─────────────────────────────────────────┐
            │  2. SCAN every artifact for forbidden   │
            │     language (Law 27, Law 28)          │
            │     — scripts/enforce_law27.py         │
            └────────────────────┬────────────────────┘
                                 │
                      forbidden? │  yes
              ┌──────────────────┴──────────────────┐
              │                                     │ no
              ▼                                     ▼
   ┌──────────────────────┐           ┌──────────────────────┐
   │  3. REPLACE          │           │  4. CLOSE — artifact  │
   │     (typed wrappers, │           │     may ship         │
   │      Law 29 enums)   │           └──────────────────────┘
   └──────────┬───────────┘
              │
              ▼
   ┌──────────────────────┐
   │  3a. If replacement  │
   │      reveals a real   │
   │      contradiction   │
   │      (e.g. mass      │
   │      stack-up does   │
   │      not sum),       │
   │      RETRACT (P7)    │
   │      and rewrite.    │
   └──────────┬───────────┘
              │
              ▼
   ┌──────────────────────────────────────────────┐
   │  3b. Re-scan. Loop until 0 forbidden        │
   │      patterns + 0 unresolved retractions.   │
   └──────────────────────────────────────────────┘
```

The loop is monotone: it can never exit with forbidden language
present. It either closes clean, or it does not close.

---

## The 5 stages of the loop

### Stage 1 — READ

Before any artifact is shipped, the producing agent (coder, system,
or LLM) must read the governance stack. This is not optional.
`scripts/remember_governance.py` prints the read list; CI Gate 1
enforces that all read-list files exist. HONESTY_LOOP.md is added
to that read list.

The read is not a formality. Each file in the read list exists
because a specific failure occurred (see FAILURES.md). Reading
them is the only way to not re-introduce those failures.

### Stage 2 — SCAN

`scripts/enforce_law27.py` scans every artifact in the repository
for forbidden language patterns. The scan covers:

- All `.md` files (documentation)
- All `.json` files in `evidence/` and `data/` (artifacts)
- All `.ts` / `.tsx` / `.py` files (source — for string literals
  that would emit forbidden language at runtime)
- All blueprint output fixtures in `tests/fixtures/`

The forbidden patterns are defined in §"Forbidden language
patterns" below. Each pattern has a required replacement.

### Stage 3 — REPLACE

For each forbidden pattern detected, the producing agent must
either:

1. **Replace** the forbidden pattern with its required typed
   replacement (Law 29 enums), OR

2. **Retract** the claim entirely (via the Retraction Registry
   engine, P7) if the replacement would expose a real
   contradiction. For example, replacing "584 kg total mass" with
   a typed claim may reveal that no mass stack-up was ever
   computed — at which point the 584 kg claim must be retracted,
   not merely re-typed.

Replacement is the default. Retraction is the exception, used
when honest typing exposes that the underlying claim was never
supported.

### Stage 4 — CLOSE

An artifact closes the loop when:

- 0 forbidden language patterns remain (scan is clean)
- All claims carry typed wrappers (Law 29e)
- All retractions in the Retraction Registry have either been
  resolved or explicitly accepted with a stated reason
- The package maturity (Law 29d) is declared on the artifact
- The validation level (Law 29b) of every claim is declared

Closed artifacts may ship. Non-closed artifacts may not.

### Stage 5 — RE-ENTER (on reality feedback)

When reality feedback arrives (a physical test, a deployment
failure, a supplier change), the loop re-enters at Stage 1 with
the new evidence. Claims that were PLAUSIBLE may be promoted to
MEASURED (Law 26) — or they may be retracted (P7). The loop
does not end at CLOSE; it re-opens whenever reality speaks.

---

## The 10 priority engines

The consolidated review instructed: "Build these mechanisms and
stop there." The 10 engines below are the mechanisms. Each has
its own `.md` file at the repo root. Each is wired into the
Honesty Loop's SCAN and REPLACE stages.

| Priority | Engine | File | What it produces |
|---|---|---|---|
| P1 | Evidence Lineage | EVIDENCE_LINEAGE_ENGINE.md | Evidence DAG with `dependencies[]` linking each piece of evidence to its upstream sources |
| P2 | Mass Stack-up | MASS_STACKUP_ENGINE.md | Per-component mass table that must sum to the claimed total, with explicit margin |
| P3 | Interface Control | INTERFACE_CONTROL_ENGINE.md | 6 interface types (electrical, thermal, mechanical, comms, manufacturing, service) per component pair |
| P4 | Procurement | PROCUREMENT_ENGINE.md | Per-BOM-line supplier, location, part number, lead time, MOQ, revision, quotation date, import duty, shipping cost |
| P5 | Validation Level | VALIDATION_LEVEL_ENGINE.md | L0-L9 maturity assignment per claim, with required promotion evidence |
| P6 | Requirement Reconciliation | REQUIREMENT_RECONCILIATION_ENGINE.md | MANDATORY/DESIRABLE/ASPIRATIONAL/EXPERIMENTAL classification with conflict detection (e.g. CTP vs module-replacement) |
| P7 | Retraction Registry | RETRACTION_REGISTRY_ENGINE.md | Append-only registry of retracted claims, with reason, replacement, and date |
| P8 | Test Registry | TEST_REGISTRY_ENGINE.md | Every test (analytical, numerical, physical) with status, date, and link to validated claim |
| P9 | Economic Reality | ECONOMIC_REALITY_ENGINE.md | Quote-backed prices, not estimates; BloombergNEF / supplier / customs data with retrieval date |
| P10 | Thermal Envelope | THERMAL_ENVELOPE_ENGINE.md | Operating temp range, heat generation, heat rejection, ambient assumptions — per component and per assembly |

### How the engines relate to the loop

```
READ (Stage 1)
   │
   ▼
SCAN (Stage 2)
   │  ┌── P1 Evidence Lineage ──────── traces every claim back to sources
   │  ├── P2 Mass Stack-up ─────────── verifies mass totals
   │  ├── P3 Interface Control ─────── verifies every component pair has interfaces
   │  ├── P4 Procurement ───────────── verifies every BOM line has supplier traceability
   │  ├── P5 Validation Level ───────── verifies every claim has L0-L9 maturity
   │  ├── P6 Requirement Reconciliation ── verifies no MANDATORY conflicts
   │  ├── P7 Retraction Registry ────── verifies no unresolved retractions
   │  ├── P8 Test Registry ─────────── verifies every test is registered
   │  ├── P9 Economic Reality ──────── verifies every price is quote-backed
   │  └── P10 Thermal Envelope ─────── verifies thermal assumptions are explicit
   │
   ▼
REPLACE (Stage 3)  ──── uses P7 (Retraction) when honest typing exposes a real contradiction
   │
   ▼
CLOSE (Stage 4)   ──── only when all 10 engines report STATUS: PASS
   │
   ▼
RE-ENTER (Stage 5) ──── when reality feedback arrives (P8 Test Registry records the result)
```

---

## Forbidden language patterns

The scanner (`scripts/enforce_law27.py`) detects the following
patterns. Each is a Law 28 violation. The scan exits non-zero if
any are present in a Blueprint-class artifact.

### Pattern set A — "complete blueprint"

```
regex:    \bcomplete\s+(engineering\s+)?blueprint\b
replace:  "engineering concept package" | "decision package" |
          "evaluation package" | "prototype package" |
          "production package"  (per Law 29d)
```

### Pattern set B — numerical confidence

```
regex:    confidence\s*[:=]\s*\d+(\.\d+)?\s*%
          confidence\s*[:=]\s*0\.\d+
          overall\s+confidence\s*[:=]\s*\d+%
replace:  validation_level: L{n}
          status: PLAUSIBLE
          evidence_strength: MODERATE
          experimental_validation: ABSENT
```

### Pattern set C — PASS / FAIL percentages

```
regex:    \d+(\.\d+)?\s*%\s*PASS
          \d+(\.\d+)?\s*%\s*FAIL
          score\s*[:=]\s*\d+(\.\d+)?\s*%
          readiness\s*[:=]\s*\d+(\.\d+)?\s*%
replace:  STATUS: PASS | PASS_WITH_CONDITIONS | MARGINAL | BLOCKED | REJECTED
```

### Pattern set D — "simulation" mislabeling

```
regex:    simulation\s*[:=]\s*\d+\s*tests?    (when tests are analytical estimates)
replace:  analytical_estimates: N checks, STATUS: ...
          numerical_simulations: N tests, STATUS: ...
          physical_validations: N tests, STATUS: ...
```

Detection of pattern set D requires semantic context — the scanner
checks the surrounding text for governing-equation keywords (FEA,
CFD, finite-element, Navier-Stokes, heat equation) and flags
mismatches.

### Pattern set E — uncalibrated probability

```
regex:    probability\s*[:=]\s*\d+(\.\d+)?\s*%
          certainty\s*[:=]\s*\d+(\.\d+)?\s*%
          reliability\s*[:=]\s*\d+(\.\d+)?\s*%
replace:  (per Law 27) — forbidden entirely unless labeled
          SIMULATION_INTERNAL and confined to a Monte Carlo block
```

### Allowlist — where the patterns are permitted

The scanner respects an allowlist. The following locations are
exempt from the forbidden-pattern check:

- `FAILURES.md` — historical failure records may quote the
  forbidden language they are reporting on. Quotes are bracketed
  by `>` (markdown blockquote) or fenced code blocks.
- `HONESTY_LOOP.md` — this document, which defines the patterns.
- `BLUEPRINT_CONSTITUTION.md` — Laws 27-29 quote the patterns
  they forbid, inside fenced code blocks.
- `tests/fixtures/forbidden_language_*.json` — fixtures used by
  the scanner's own tests, which must contain the patterns to
  verify detection.

Every other file is scanned without exemption.

---

## Loop closure gate (Gate 11)

The Honesty Loop adds one new gate to the AEP pipeline. It sits
*after* Gate 10 (Postmortem) and *after* Gate 10.5 (Kill-Test).

### Gate 11 — Loop Closure Gate

**Question:** Has the artifact closed the Honesty Loop?

**Required checks:**

1. `scripts/enforce_law27.py` exits 0 on the artifact (no
   forbidden language patterns detected).
2. Every claim in the artifact carries a typed wrapper (Law 29e):
   `validationLevel`, `evidenceStrength`, `experimentalValidation`,
   `status`, `evidenceIds[]`.
3. The package maturity (Law 29d) is declared on the artifact.
4. All 10 priority engines have produced output for the artifact
   and each reports `STATUS: PASS` or `STATUS: PASS_WITH_CONDITIONS`.
5. The Retraction Registry (P7) contains no unresolved retractions
   for this artifact.

**Pass criteria:** All 5 checks pass. STATUS: PASS.

**Failure:** Work is rejected. The artifact remains in the loop
at Stage 3 (REPLACE) or Stage 3a (RETRACT) until closure.

**Artifact:** HONESTY_LOOP_CLOSURE_RECORD (JSON, stored in
`evidence/gates/gate_11_honesty_loop.json`).

---

## The single direction to the coder

```text
You are not permitted to ship "58% confidence."
You are not permitted to ship "85.7% PASS."
You are not permitted to ship "complete blueprint."

You are permitted to ship:
    validation_level: L2
    status: PLAUSIBLE
    evidence_strength: MODERATE
    experimental_validation: ABSENT
    package_maturity: EVALUATION

That is less impressive. It is also honest.
The honest answer is the only answer that ships.
```

---

## Relationship to existing governance

| Existing rule | Honesty Loop relationship |
|---|---|
| Rule 7 (BLUEPRINT_CONSTITUTION.md) | Honesty Loop operationalizes: forbids the most common disguise (numerical certainty) |
| Law 26 (epistemic separation) | Honesty Loop requires typed status per level — POSSIBILITY/PLAUSIBILITY/SIMULATION/MEASUREMENT/REALITY each carry a `validation_level` |
| EP-16 (no false certainty) | Honesty Loop supersedes: replaces `Confidence.value` numeric field with typed status block |
| Principle 4 (confidence never 1.0) | Honesty Loop strengthens: numerical certainty is never assigned without experimental validation, regardless of value |
| Law 8 (CONSTITUTION.md — verification standard) | Honesty Loop extends: requires positive AND negative evidence before any `STATUS: PASS` verdict |
| Gate 10.5 (Kill-Test) | Honesty Loop adds Gate 11 (Loop Closure) — kill tests must be registered in P8 Test Registry before closure |

The Honesty Loop does not replace any existing rule. It enforces
them by making the forbidden patterns mechanically detectable
and the required replacements mechanically verifiable.

---

## Pre-stated falsifier (EP-4)

**Claim:** The Honesty Loop eliminates false precision from
Blueprint outputs.

**Falsifier:** An artifact that passes Gate 11 (Loop Closure)
but is later found to contain a claim that should have been
labeled `STATUS: REJECTED` — i.e., the typed wrappers are
present but the underlying claim is unsupported.

**Status:** PENDING. The loop is documented; mechanical
enforcement (scanner + tests + CI gate) is wired in this commit.
The first real test is the next Blueprint the system produces.

---

## Status

The Honesty Loop is **active** as of this commit. The 10 priority
engines are **specified** (their `.md` files exist) but **not
implemented** in code — per the consolidated review's instruction:
"Build these mechanisms and stop there." Building the `.md`
specifications is the mechanism. Code implementation awaits
Gate 1 (Comprehension) for each engine, run as a separate AEP
work item.

The scanner (`scripts/enforce_law27.py`) and the test
(`tests/test_honesty_loop.py`) are **implemented** and **wired
into CI** as Gate 4 of the workflow. The loop is mechanically
enforced from this commit forward.
