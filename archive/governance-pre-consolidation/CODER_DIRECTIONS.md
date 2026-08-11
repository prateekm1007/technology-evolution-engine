# CODER_DIRECTIONS

**Status:** Consolidated directions for the coder.
**Location:** TEE repo root.
**Phase:** Post-BP-2.

> Read patents. Read recalls. Read engineering reports. Read academic
> papers. Read standards. Read complaints. Read bankruptcy filings.
> Read maintenance manuals. Read supplier catalogues. Read regulations.
> Read incident reports. Read postmortems. Then build.
>
> Because the enemy is not lack of intelligence.
> The enemy is accumulated ignorance.
> And your job is to reduce it, one blueprint at a time.
> — CEO directive, BP-1

---

## Purpose

This document consolidates all governance rules, engineering principles,
and development directives into a single reference for the coder. It
exists so that future development sessions do not lose the intellectual
discipline accumulated across Phases 1-17 and BP-0/BP-1/BP-2.

---

## The 4 governance layers

| Layer | Document | What it governs |
|---|---|---|
| Research process | CONSTITUTION.md (Laws 1-8 + Rule 8) | Theory, falsification, evidence hierarchy |
| Documentation | EVIDENCE_STANDARDS.md (EP-1 to EP-16) | Documentation claims, no self-grading, no post-hoc thresholds |
| Architecture | REACHABILITY_CONSTITUTION.md (Rules 1-6) | Classification, state, mechanisms, boundaries, failures, simplicity |
| Product | BLUEPRINT_CONSTITUTION.md (20 Laws + Rule 7) + ENGINEERING_PRINCIPLES.md (10 Principles) | Blueprint output, engineering process |

---

## The 7 rules that supersede all others

1. **Rule 7** (BLUEPRINT_CONSTITUTION.md): Never pretend uncertainty is certainty.
2. **Law 1** (BLUEPRINT_CONSTITUTION.md): Reality dominates opinion.
3. **Law 5** (BLUEPRINT_CONSTITUTION.md): Every recommendation requires alternatives.
4. **Law 20** (BLUEPRINT_CONSTITUTION.md): Reality always wins.
5. **EP-1** (EVIDENCE_STANDARDS.md): No claim without an artifact.
6. **EP-5** (EVIDENCE_STANDARDS.md): No self-grading.
7. **EP-12** (EVIDENCE_STANDARDS.md): Diff before commit, always.

---

## The 18 required engines

Every blueprint MUST include output from all 18 engines — the
8 original engines (BP-1) plus the 10 Honesty Loop priority
engines (BP-2, post-consolidated-review).

### Original 8 engines (BP-1)

| Engine | File | Priority | What it produces |
|---|---|---|---|
| Evidence | evidence-engine.ts | P0 | Ranked sources (A-I); evidence DAG delegated to Evidence Lineage (P1 Honesty Loop) |
| Assumption | assumptions-engine.ts | P1 | Explicit assumptions with impact and falsifiers |
| Unknowns | unknowns-engine.ts | P2 | What the system does not know |
| Alternatives | alternatives-engine.ts | P3 | PRIMARY + A + B + C for every component |
| Constraint Graph | constraint-graph.ts | P4 | DAG of constraint propagation |
| Validation Level | (P5 Honesty Loop, supersedes Confidence) | P5 | L0-L9 maturity assignment per claim (Law 29b) — REPLACES the BP-1 confidence-engine |
| Simulation | simulation-engine.ts | P7 | Stress tests with STATUS enum (Law 29a), registered in Test Registry (P8) |
| Failure | blueprint-data.ts + FAILURE_LIBRARY.md | P4(E) | Failure modes with scenarios, probability, mitigation |

### Honesty Loop 10 priority engines (post-BP-2)

| Engine | File | Priority | What it produces |
|---|---|---|---|
| Evidence Lineage | EVIDENCE_LINEAGE_ENGINE.md | P1 | Evidence DAG with `dependencies[]` — ancestry, not just citation |
| Mass Stack-up | MASS_STACKUP_ENGINE.md | P2 | Per-component mass table that sums to total, with margin |
| Interface Control | INTERFACE_CONTROL_ENGINE.md | P3 | 6 interface types per component pair (electrical/thermal/mechanical/comms/manufacturing/service) |
| Procurement | PROCUREMENT_ENGINE.md | P4 | Supplier + part number + lead time + MOQ + quotation date + landed cost per BOM line |
| Validation Level | VALIDATION_LEVEL_ENGINE.md | P5 | L0-L9 maturity per claim, with promotion path and evidence gates |
| Requirement Reconciliation | REQUIREMENT_RECONCILIATION_ENGINE.md | P6 | MANDATORY/DESIRABLE/ASPIRATIONAL/EXPERIMENTAL classification with conflict detection |
| Retraction Registry | RETRACTION_REGISTRY_ENGINE.md | P7 | Append-only ledger of retracted claims, with reason and replacement |
| Test Registry | TEST_REGISTRY_ENGINE.md | P8 | Every test (analytical/numerical/physical) with type, method, result, evidence |
| Economic Reality | ECONOMIC_REALITY_ENGINE.md | P9 | Quote-backed prices with staleness tracking; estimates labeled, not disguised |
| Thermal Envelope | THERMAL_ENVELOPE_ENGINE.md | P10 | Operating range + heat generation + rejection + failure thresholds |

**A blueprint missing any of these 18 engines is incomplete
and cannot close the Honesty Loop (Gate 11).**

### Forbidden BP-1 patterns (per Law 27, 28)

- `confidence: 0.58` or `confidence = 58%` — forbidden. Use `validation_level: L2` (Law 29b) instead.
- `85.7% PASS` — forbidden. Use `STATUS: PASS_WITH_CONDITIONS` (Law 29a) instead.
- `complete engineering blueprint` — forbidden. Use `evaluation package` or `prototype package` (Law 29d) instead.
- `simulation: 18 tests` when tests are analytical estimates — forbidden. Use `analytical_estimates: 18 checks` (Law 28d) instead.

See `HONESTY_LOOP.md` and `scripts/enforce_law27.py` for the full
forbidden-language scanner.

---

## The 7 engineering review questions

Every blueprint review must answer:

1. **Physics:** Can this work?
2. **Economics:** Can somebody pay for this?
3. **Manufacturing:** Can somebody build this?
4. **Regulation:** Can somebody sell this?
5. **Maintenance:** Can somebody repair this?
6. **Scaling:** Can millions of units exist?
7. **Human factors:** Can ordinary people use this?

---

## The evidence hierarchy

Every assertion carries a ranked source:

| Rank | Source | Weight |
|---|---|---|
| A | Physics and experiments | 1.00 |
| B | Regulatory filings | 0.95 |
| C | Patents | 0.90 |
| D | Academic literature | 0.85 |
| E | Manufacturer specifications | 0.80 |
| F | Industry reports | 0.70 |
| G | User reports | 0.60 |
| H | General web sources | 0.50 |
| I | LLM inference | 0.20 |

Assertions without evidence are forbidden. Assertions with only LLM
inference (rank I) must be labeled "unverified — inference only."

---

## The 8-layer knowledge pyramid

Per CONSTITUTION.md Rule 8: learn from reality before creating reality.

| Layer | What to study | Example sources |
|---|---|---|
| 1 | Existing products | John Deere, Naio, FarmWise, DJI Agriculture |
| 2 | Failed products | FarmWise bankruptcy, Bear Flag acquisition, Iron Ox |
| 3 | Patents | US Patent 10,856,921 (navigation), US 11,201,896 (sensors) |
| 4 | Academic research | Shamshiri 2018 (review), Bayati 2022 (navigation) |
| 5 | Open-source projects | ROS2 Humble, Nav2, BehaviorTree.CPP |
| 6 | Manufacturing knowledge | IPC-A-610, ISO 8608, Wright's Law |
| 7 | Economic reality | BloombergNEF battery prices, PV Magazine solar prices |
| 8 | Regulation | India MV Act, EU Machinery Directive, EN ISO 13849-1 |

No blueprint may be produced without consulting all 8 layers.

---

## The 4 eras

| Era | Objective | Proof | Status |
|---|---|---|---|
| 1 | Knowledge organization | "I can build this." | **ACHIEVED** (BP-0/BP-1/BP-2) |
| 2 | Optimization | "I can build this more efficiently." | Not started |
| 3 | Discovery | "I never considered building this." | Not started |
| 4 | Invention | "Nobody considered building this." | Aspirational |

Era 1 is proven: the blueprint is concrete enough for a manufacturer
to evaluate. Era 2 requires the system to compare designs and select
the best. Era 3 requires proposing combinations humans didn't consider.
Era 4 is the north star.

---

## Development rules

### Rule 1: Never optimize for impressiveness. Optimize for truth.

### Rule 2: Never optimize for novelty. Optimize for usefulness.

### Rule 3: Never optimize for complexity. Optimize for clarity.

### Rule 4: Never optimize for elegance. Optimize for reality.

### Rule 5: Nothing is ever accepted without evidence.

---

## The architectural rule

The Blueprint is a **compiler**. Not a chatbot, not a search engine,
not a report generator, not a slide deck generator, not a CAD package,
not an LLM wrapper. It takes an idea as input and produces a complete,
executable blueprint as output.

---

## Current state (as of Honesty Loop v1.0, post-BP-2)

### Package output: 22 sections

1. Executive Summary (verdict, capital, break-even, risk, unit cost)
2. Classification
3. State Vector (7 dimensions)
4. Constraints (9 with severity/probability/mitigation)
5. Dependency Graph (critical path, bottlenecks)
6. Bill of Materials (16 items, $2,373, real suppliers)
7. Cost Model ($1.2M capital, $3K unit, 3.3-year break-even)
8. CAD Specification (dimensions, materials, tolerances, joints)
9. Manufacturing Plan (14 steps, 6h/unit, 92% yield)
10. Regulatory Pathway (India, US, EU)
11. Deployment Plan (3 phases, 36 months)
12. Failure Analysis (7 modes, risk 0.4)
13. Validation Level Assessment (per claim, L0-L9; replaces confidence percentage per Law 27)
14. Evidence (20 sources, ranks A-H, weights)
15. Assumptions (10 with falsifiers)
16. Unknowns (10 explicit, including CC6 gaps)
17. Alternatives (5 components × 4 options)
18. Engineering Completeness (8 subsystems, 66% avg, 26 missing → now specified)
19. Analytical Estimates + Simulations (18 entries in Test Registry, P8: 3 FAIL, 15 PASS/PASS_WITH_CONDITIONS — STATUS: MARGINAL for the package)
20. Constraint Graph (20 nodes, 19 edges, 4 critical paths)
21. Explainability (5 recommendations with Why/WhyNot/WhatChanged/WhatFailed/Alternatives)
22. Production Specifications (26 items, STATUS: PASS_WITH_CONDITIONS; 4 require physical testing)

### Honest metrics (per Law 27, 28 — no numerical certainty)

- **Validation level**: most claims at L1-L2; L4+ for cell chemistry (single-cell test); L0 for serviceability claim
- **Status (overall package)**: PASS_WITH_CONDITIONS — 2 FATAL consistency violations (now retracted via P7), 3 simulation FAILs (now retracted via P7)
- **Test registry**: 18 entries (3 FAIL, 15 PASS or PASS_WITH_CONDITIONS) — `STATUS: MARGINAL` for the package
- **Production readiness**: 22 of 26 items fully specified, 4 REQUIRES_TESTING — `STATUS: PASS_WITH_CONDITIONS`
- **Engineering completeness**: 8 subsystems tracked, gaps closing — `STATUS: MARGINAL`
- **Evidence**: 20 sources, rank distribution: A×2, B×1, C×4, D×8, E×3, F×2 — `EVIDENCE_STRENGTH: STRONG`
- **Assumptions**: 10 with falsifiers (each linked to a kill-test)
- **Unknowns**: 10 explicit (including 4 REQUIRES_TESTING items)
- **Alternatives**: 20 total paths (5 components × 4 options)
- **Package maturity**: EVALUATION (per Law 29d — not PRODUCTION; physical validation absent)
- **Version**: immutable, SHA-256 verified

### Domain restriction

Autonomous agricultural systems ONLY. No aerospace, pharma,
semiconductors, automobiles, or multi-domain support.

---

## Next steps (CEO's decision)

1. **Era 2: Optimization** — compare multiple designs, select best based on evidence
2. **Second vertical slice** — test architecture generalization (CEO's call)
3. **Close 4 REQUIRES_TESTING items** — FEA, PID tuning, safety certification (requires physical hardware)
4. **Deeper knowledge pyramid** — more evidence from Layers 1-8 (patents, recalls, academic)
5. **Negative knowledge graph** — accumulate failure data from real products

---

## The moat

Existing companies possess one layer:
- Autodesk has CAD
- Ansys has simulation
- McKinsey has strategy
- Palantir has data integration
- SAP has supply-chain management

The Blueprint connects all layers simultaneously:

```text
physics → economics → regulation → manufacturing → capital → logistics → execution → design
```

That integration is the moat.

---

## Final instruction to the coder

```text
Your job is not to impress people.
Your job is to make them trust the machine.
A beautiful hallucination is failure.
An ugly truth is success.
```

Read everything. Then build. Then verify. Then iterate.

---

## Stage Progression (refined by CEO, post-WCP-1)

> Do not ask the machine to invent yet.
> Ask it to surprise you first.
> — CEO directive, post-WCP-1

| Stage | Objective | Success criterion | Status |
|---|---|---|---|
| 1 (BP-1) | Build something that exists | "Could an expert build it?" | **DONE** (solar irrigation robot) |
| 2 (BP-2) | Build something that exists, improved | "Is it objectively better?" | Not started |
| 3 (BP-3) | Combine mature technologies | "Why didn't people build this earlier?" | Not started |
| 4 (BP-4) | Explore the edge of the possible | "Is this reachable?" | Not started |
| 5 (BP-5) | Attempt invention | "Can the machine discover something genuinely new?" | Aspirational |

**The test case for Stage 3 (boundary between recombination and invention):**

Adaptive micro-irrigation mesh — a modular, solar-powered irrigation
network for small farms. The question is not "can the system imagine
something extraordinary?" but "can the system identify a better
configuration than a human would have selected?"

**Do NOT skip stages.** The sequence that makes The Blueprint
different from an LLM wrapper is:

```text
failure → boundary → classification → mechanism → constraint →
reachability → construction
```

If you skip those steps, you lose the moat.
