# REACHABILITY_REPORT_TEMPLATE

**Status:** Phase 17 Deliverable 10.
**Location:** repo root.
**Phase:** 17.

> This is the point at which you stop saying 'We have a theory.'
> And start saying 'Here is the machine. Build this object.'
> — CEO directive, Phase 17

---

## Purpose

This document is the template for the Reachability Report — the
final output of the Blueprint Engine. When a builder or enterprise
enters an idea, the system returns a Reachability Report that
specifies the idea completely enough to begin execution.

This template is filled by the Blueprint Engine using the outputs
of all downstream engines (Phase 16A). The example blueprint
(EXAMPLE_BLUEPRINT_001.md) is an instance of this template.

---

## Template

```text
═══════════════════════════════════════════════════════════════
                    REACHABILITY REPORT
═══════════════════════════════════════════════════════════════

Blueprint ID: [BP-XXX]
Date: [YYYY-MM-DD]
Idea: [IdeaInput.title]

───────────────────────────────────────────────────────────────
EXECUTIVE SUMMARY
───────────────────────────────────────────────────────────────

Verdict: [FEASIBLE | FEASIBLE_WITH_RISK | NOT_FEASIBLE]

Required capital: $[X.X million]
Time horizon: [X.X years]
Primary bottleneck: [bottleneck description]
Probability of success: [0.XX]
Recommended path: [Path description]

───────────────────────────────────────────────────────────────
1. CLASSIFICATION
───────────────────────────────────────────────────────────────

Dominant class: [DISCOVERY | EMERGENCE | SCALING | COORDINATION | RECOMBINATION]
Confidence: [0.XX]

Secondary class: [class or NONE]
Confidence: [0.XX]

Evidence:
  - [evidence 1]
  - [evidence 2]
  - [evidence 3]

───────────────────────────────────────────────────────────────
2. STATE VECTOR
───────────────────────────────────────────────────────────────

Scientific state:        [0.X]  [interpretation]
Technological state:     [0.X]  [interpretation]
Manufacturing state:     [0.X]  [interpretation]
Regulatory state:        [0.X]  [interpretation]
Economic state:          [0.X]  [interpretation]
Coordination state:      [0.X]  [interpretation]
Infrastructure state:    [0.X]  [interpretation]

───────────────────────────────────────────────────────────────
3. CONSTRAINTS
───────────────────────────────────────────────────────────────

Constraint load: [0.XX]  [LOW < 0.3 | MODERATE 0.3-0.6 | HIGH > 0.6]

Critical constraints (severity > 0.6):
  1. [CON-XXX] [type] severity [0.X] probability [0.X]
     Mitigation: [mitigation]
  2. [CON-XXX] [type] severity [0.X] probability [0.X]
     Mitigation: [mitigation]

All constraints:
  [list of all constraints with type, severity, probability]

───────────────────────────────────────────────────────────────
4. DEPENDENCY GRAPH
───────────────────────────────────────────────────────────────

Critical path: [component] → [component] → [component] → [idea]
Critical path length: [N] stages
Bottlenecks: [component IDs on critical path with maturity < 0.8]

Graph:
  [ASCII art of dependency graph]

───────────────────────────────────────────────────────────────
5. BILL OF MATERIALS
───────────────────────────────────────────────────────────────

BOM cost: $[X,XXX] at quantity [1000]

| # | Component | Qty | Unit cost | Total | Supplier |
|---|-----------|-----|-----------|-------|----------|
| 1 | [name]    | [N] | $[XXX]    | $[XX] | [name]   |
|...|           |     |           |       |          |
|   | TOTAL     |     |           | $[XX] |          |

───────────────────────────────────────────────────────────────
6. COST MODEL
───────────────────────────────────────────────────────────────

Capital requirement: $[X.X million]
Unit cost: $[X,XXX]
Operating cost: $[XXX/year]
Expected revenue: $[X,XXX/year]
Break-even: [X.X] years at [N] units/year

Revenue model: [purchase | leasing | subscription]
Willingness to pay: [small farm: $X | medium farm: $Y | cooperative: $Z]

Cost breakdown:
  BOM:                  $[X,XXX]
  Assembly labor:       $[XXX]
  Manufacturing overhead: $[XXX]
  QC + testing:         $[XXX]
  Logistics:            $[XX]
  Total unit cost:      $[X,XXX]

───────────────────────────────────────────────────────────────
7. CAD SPECIFICATION
───────────────────────────────────────────────────────────────

Dimensions: [L x W x H] mm, [weight] kg
Materials: [list of materials with mass]
Tolerances: [list of critical tolerances]
Joints: [list of joint types and specifications]

[Full CAD specification per CAD_SPECIFICATION_SCHEMA.md]

───────────────────────────────────────────────────────────────
8. MANUFACTURING PLAN
───────────────────────────────────────────────────────────────

Assembly steps: [N] steps, [X] hours per unit
Suppliers: [N] suppliers, lead time [X] weeks
Yield estimate: [XX]%
Throughput: [N] units/day (single shift)

[Full manufacturing plan per MANUFACTURING_ENGINE.md]

───────────────────────────────────────────────────────────────
9. REGULATORY PATHWAY
───────────────────────────────────────────────────────────────

Primary jurisdiction: [jurisdiction]
Risk: [0.X]
Certification time: [X months]

| Jurisdiction | Authority | Requirement | Risk |
|---|---|---|---|
| [jurisdiction] | [authority] | [requirement] | [0.X] |
|...|             |             |       |

───────────────────────────────────────────────────────────────
10. DEPLOYMENT PLAN
───────────────────────────────────────────────────────────────

Phase 1 (Pilot): [months 1-N], [scope], [success criteria]
Phase 2 (Early deployment): [months N-M], [scope], [success criteria]
Phase 3 (Scale): [months M-X], [scope], [success criteria]

Staffing: [N] engineers, [N] manufacturing, [N] field service
Budget: $[X.X million] total
  - R&D: $[XXX]
  - Manufacturing setup: $[XXX]
  - Field service: $[XXX]
  - Regulatory: $[XXX]
  - Operations: $[XXX]

───────────────────────────────────────────────────────────────
11. FAILURE ANALYSIS
───────────────────────────────────────────────────────────────

Overall failure risk: [0.X]
Highest risk: [failure type] (severity [0.X], probability [0.X])

| Type | Scenario | Severity | Probability | Mitigation |
|---|---|---|---|---|
| [type] | [scenario] | [0.X] | [0.X] | [mitigation] |
|...|     |           |       |            |

Risk mitigation priority:
  1. [highest priority failure]
  2. [second priority]
  3. [third priority]

───────────────────────────────────────────────────────────────
12. SIMULATION RESULTS
───────────────────────────────────────────────────────────────

CAN_WORK:        [YES | NO]  confidence [0.X]
  Evidence: [evidence]
  Blocking: [blocking factors or NONE]

CAN_BUILD:       [YES | NO]  confidence [0.X]
  Evidence: [evidence]
  Blocking: [blocking factors or NONE]

CAN_MANUFACTURE: [YES | NO]  confidence [0.X]
  Evidence: [evidence]
  Blocking: [blocking factors or NONE]

CAN_MAINTAIN:    [YES | NO]  confidence [0.X]
  Evidence: [evidence]
  Blocking: [blocking factors or NONE]

CAN_SCALE:       [YES | NO]  confidence [0.X]
  Evidence: [evidence]
  Blocking: [blocking factors or NONE]

Overall simulation pass rate: [N/5]

───────────────────────────────────────────────────────────────
13. EXPLANATION
───────────────────────────────────────────────────────────────

Mechanism: [MECH-XXX from MECHANISM_REGISTRY_V2.md]
Evidence:
  - [evidence 1]
  - [evidence 2]
Assumptions:
  - [assumption 1]
  - [assumption 2]
Boundaries:
  - [boundary 1]
  - [boundary 2]

═══════════════════════════════════════════════════════════════
                    END OF REPORT
═══════════════════════════════════════════════════════════════
```

---

## Business product variant

For enterprise customers, the report is condensed to:

```text
═══════════════════════════════════════════════════════════════
                    REACHABILITY REPORT
═══════════════════════════════════════════════════════════════

Idea: [IdeaInput.title]

THIS IS [POSSIBLE | POSSIBLE_WITH_RISK | NOT_POSSIBLE].

Required capital: $[X.X million].
Time horizon: [X.X] years.

Primary bottleneck: [bottleneck description].

Probability of success: [0.XX]

Recommended path: [Path X — description].

Simulation results: [N/5 passed]
  CAN_WORK:        [YES/NO]
  CAN_BUILD:       [YES/NO]
  CAN_MANUFACTURE: [YES/NO]
  CAN_MAINTAIN:    [YES/NO]
  CAN_SCALE:       [YES/NO]

Highest risk: [failure type] — [mitigation summary].

═══════════════════════════════════════════════════════════════
```

---

## What this template does NOT do

- It does not fill itself. The Blueprint Engine fills it using downstream engine outputs.
- It does not guarantee the report is correct. The report is a compilation of estimates; correctness depends on the quality of the estimates.
- It does not handle multi-idea reports. One idea = one report.
- It does not modify the frozen formula or any prior architecture.

---

## Pre-stated falsifier (EP-4)

**Claim:** This report template, when filled, provides sufficient information for a builder or enterprise to decide whether to proceed with execution.

**Falsifier:** A decision-maker who receives a filled report but cannot make a decision because of missing information — i.e., the report does not include a field needed for the go/no-go decision.

**Status:** PENDING. The example blueprint (EXAMPLE_BLUEPRINT_001.md) is an instance of this template. Whether it is sufficient for a real decision-maker is untested.
