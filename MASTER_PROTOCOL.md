# MASTER_PROTOCOL

> The purpose of a package is not to describe an idea.
> The purpose of a package is to remove the next expensive risk.
> — CEO directive, market feedback integration

This is the single document that governs how the system produces
engineering packages. The coder reads this document and nothing else
before producing a package. The protocol decides. The coder executes.

---

## The commercial specification

You are not writing reports. You are reducing uncertainty.

You are not producing documents. You are producing decisions.

You are not rewarded for complexity. You are rewarded for eliminating
the next risk.

Every page must answer: "Would someone spend money because this page
exists?"

A customer does not buy a PDF. A customer buys the elimination of
uncertainty. The package exists to remove the next expensive risk so
the customer can spend the next dollar intelligently.

---

## The single command

```
INPUT:  A problem statement (e.g., "Build an EV battery pack")
OUTPUT: MASTER_PACKAGE.md → product/PRODUCT.pdf
        A single document with 12 sections + a Next Money Page
```

The coder does not decide what to produce. The protocol defines the
structure. The coder fills each section honestly.

---

## The 12 Laws

These laws are constitutional. A package that violates any law is
REJECTED. No exceptions.

### LAW 1 — Product identity

Every package shall declare exactly one maturity level:

```
DISCOVERY
CONCEPT
EVALUATION
DETAILED DESIGN
PRE-PROTOTYPE
PROTOTYPE
VALIDATED DESIGN
PRODUCTION
```

A package may never claim a higher level than its evidence permits.
A package with no physical validation cannot claim PROTOTYPE or above.
A package with no prototype cannot claim VALIDATED DESIGN or above.

### LAW 2 — Arithmetic closure

Every package shall contain:
- energy budget
- mass budget
- cost budget
- thermal budget
- manufacturing budget

All numbers must reconcile. The mass stack-up must sum to the total.
The cost BOM must sum to the total. The energy budget must balance
(generation vs rejection). No unresolved contradictions are permitted.
A contradiction blocks the package (§Consistency).

### LAW 3 — Epistemic closure

Every claim shall possess:
- claim (the statement)
- source (where it came from)
- method (how it was derived)
- validation level (L0-L9)
- status (PASS / PASS_WITH_CONDITIONS / MARGINAL / BLOCKED / REJECTED)
- blocking condition (what prevents promotion)

No numerical confidence is permitted (per Law 27 of the prior
constitution, now subsumed). The typed status block is the only
sanctioned epistemic representation.

### LAW 4 — Retractions

Retractions are permanent. Retractions are never deleted. Retractions
are never hidden. A retracted claim is marked RETRACTED with a reason,
a date, and a replacement (or explicit WITHDRAWN status). The Retraction
Registry (P7) is append-only.

### LAW 5 — Thermal truth

Narrative reasoning is prohibited for thermal claims. Acceptable
methods:
- measurements (from physical tests)
- analytical models (first-principles derivation)
- 1D models (lumped-parameter)
- CFD (computational fluid dynamics)
- FEA (finite element analysis)
- physical experiments

The method must be recorded. "We believe it will be fine" is not
thermal truth.

### LAW 6 — Cost truth

Every cost line shall declare one of:
- QUOTED (supplier quotation with date + expiry)
- CATALOG (published list price)
- ESTIMATED (engineering estimate, labeled as such)

A PRODUCTION package requires all lines QUOTED. An EVALUATION package
permits ESTIMATED lines but they must be labeled and counted.

### LAW 7 — Interface control

Every package shall include:
- mechanical interfaces
- electrical interfaces
- software interfaces (if applicable)
- thermal interfaces
- communication interfaces

Each interface has a type, a status, and evidence. An undeclared
interface is a future field failure.

### LAW 8 — Safety

Every package shall contain:
- standards (ISO, IEC, SAE, UN, etc.)
- abuse cases (what happens when it's misused)
- propagation cases (thermal runaway propagation analysis)
- failure analysis (FMEA or equivalent)
- certification paths (regulatory approval roadmap)

### LAW 9 — Manufacturing

Every package shall contain:
- process sequence (step-by-step assembly)
- tooling (what equipment is required)
- yield (expected pass rate)
- failure modes (what can go wrong in production)
- quality gates (inspection points)

### LAW 10 — Kill tests

The system does not ask "Can we build it?" The system asks "How do we
kill it?"

Every package must contain kill tests. Each kill test has:
- KT-ID (KT-01, KT-02, ...)
- claim (the assumption being tested)
- test (the method)
- measurement (what is measured)
- failure threshold (the pass/fail boundary)
- consequence (what happens if it fails)

Example:
```
KT-01
Claim: 1.5C charging supported
Test: physical cell cycle test
Measurement: cell temperature
Failure threshold: 55°C
Consequence: charge rate reduced to 1.2C
```

A kill test that FAILS triggers a retraction (Law 4) and a revision
of the affected claim.

### LAW 11 — Intellectual-property posture

Every package shall contain:
- relevant patents (active + expired)
- known claim families (who owns what)
- known litigation history (has this been sued over)
- restricted zones (where can this not be sold)
- lawyer review requirements (what needs legal sign-off)

### LAW 12 — Next-spend protocol

Every package shall answer:
- What should we do next?
- What will it cost?
- What will we learn?
- What decision becomes possible?
- What could kill the project?

This is the Next Money Page (see §The Next Money Page below). The
package does not end at a verdict. It ends at a decision.

### LAW 13 — Independent recomputation

Every headline number in a package shall be independently recomputed
from raw line items by a verifier that is architecturally separate
from the generation path. The verifier never sees the document's
stated totals — it reads only the raw inputs (BOM unit costs ×
quantities, mass unit weights × counts, energy inputs) and recomputes.

Any diff > 0 blocks the PASS verdict. Not "flags for review" — blocks.

The verifier is `scripts/verify_arithmetic.py`. It runs in CI as
Gate 2.75, between the Law 27 scan and the thermal model check.

**Definition of done:** the verifier must independently surface
arithmetic errors without being told they exist. If the verifier
passes, the numbers reconcile. If it fails, the package cannot ship
regardless of how polished the presentation is.

This law addresses the root cause of every arithmetic error found
in the audit: the system was checking its own arithmetic against
itself, not against an independent recomputation.

---

## The pay bar (market feedback, 2026-08-03)

> If I committed the next $25k–$100k (quotes, CFD, fixture, or prototype
> cells), this package would tell me exactly what to build, what to
> measure, what would kill the design, and what the residual risks are —
> with every critical number either measured, quoted, or explicitly
> marked as blocking.

A customer pays for an engineering design package when the document
**removes the next expensive risk**, not when it narrates a good idea.
The 12 criteria below define the minimum excellence bar. All 12 are
required. Miss any of criteria 2, 5, 6, 7, or 10 → the customer does
not pay for hardware design (at most a small fee for process/template).

### The 12 excellence criteria (all required)

| # | Criterion | What "excellent" looks like |
|---|-----------|------------------------------|
| 1 | **Identity** | Labeled DETAILED DESIGN / pre-prototype, not "concept" or "complete blueprint" |
| 2 | **Arithmetic closure** | Energy, mass, voltage, $/kWh, C-rate one coherent set; mass stack-up sums to stated pack mass |
| 3 | **Epistemic honesty** | Every critical claim has level (L1–L4 or equivalent); no silent upgrades |
| 4 | **Retraction discipline** | Failed claims in a registry with replacement specs |
| 5 | **Thermal truth** | Charge/discharge envelope backed by model + method (1D network minimum; CFD preferred) or cell/fixture data |
| 6 | **Quoted cost** | Cell + cold plate + contactors + major HV parts: dated supplier quotes (or 3-bid range); labor not a pure guess |
| 7 | **Interfaces** | ICD: mechanical, HV, LV, coolant, CAN/BMS signals, mounting loads |
| 8 | **Safety path** | Abuse/propagation/IP/transport mapped to named tests and pass/fail limits |
| 9 | **Manufacturing path** | Sequence, critical processes (e.g. laser weld), QC gates, yield drivers — not only "≤8 h" |
| 10 | **Kill tests** | 5–10 tests that can fail the package; each with metric, method, and consequence |
| 11 | **IP posture** | Not full FTO opinion, but high-risk claim families + "do not ship without counsel" list |
| 12 | **Next-spend plan** | Ordered budget: what $X buys next and what decision it unlocks |

**Pass rule:** Meet all 12 at least at "good." Miss any of 2, 5, 6, 7, 10 → no hardware-design payment.

### Non-negotiables (deal breakers)

The customer will NOT pay for hardware design if ANY of these are true:

1. Mass/energy/cost still internally inconsistent
2. A retracted claim (e.g. 2C) reappears without new evidence
3. Serviceability is MANDATORY while architecture is non-serviceable CTP
4. "Simulation" means narrative scenarios with no equations/method
5. Cost is catalog fiction with no quote trail
6. Package claims PRODUCTION / complete blueprint without physical validation

### The 5-phase roadmap (concept → paying package)

| Phase | Goal | Duration | Exit criterion |
|-------|------|----------|----------------|
| 0 | Freeze the product identity | 3–5 days | Single requirements table everyone uses |
| 1 | Close the numbers (mass, energy, cost) | 1–2 weeks | No internal arithmetic contradictions; cost has ≤1 ESTIMATE |
| 2 | Thermal & electrical integrity | 2–4 weeks | Kill-test KT-thermal can be run by a third party from the description alone |
| 3 | Interfaces, safety, manufacturing | 2–3 weeks | Another engineer can see how it mounts, cools, communicates, gets certified |
| 4 | Kill-test suite & validation plan | 1–2 weeks | "Next $X" buys KT-01/02 or RFQ closure — explicit |
| 5 | Package hardening | 1 week | Meets the 12-criterion bar → customer would pay at detailed-design rate |

### What the customer pays at each stage

| Stage | Product | Pays? |
|-------|---------|-------|
| Now (EVALUATION concept) | Protocol exemplar | Small fee or free (method demo) |
| After Phase 1–2 | Numbers-closed concept + thermal model | Modest professional fee |
| After Phase 3–4 | Pre-prototype design package | **Yes — hardware design package rate** |
| After prototype + test data | Validated design | Higher (data-backed) |
| Full CAD + certified path | OEM-style program | Program pricing, not a PDF SKU |

### The highest-ROI stretch

Phase 1 (mass + quotes) + Phase 2 (thermal envelope) — that pair moves
the package from "impressive process" to "something an engineer would
buy before spending on hardware."

---

## The package structure (12 sections + Next Money Page)

Every package MUST contain all sections, in order. A section that
cannot be filled is marked BLOCKED with a stated reason — it is never
skipped.

### 0. PURPOSE
What are we building and why? Primary objective. Success metric =
"a customer can spend the next dollar intelligently." Maturity level
(Law 1).

### 1. REQUIREMENTS
List every requirement. Classify: MANDATORY / DESIRABLE / ASPIRATIONAL
/ EXPERIMENTAL. Two MANDATORY conflicts block the package.

### 2. EVIDENCE
Existing products, failed products, patents, academic literature,
standards, supplier data. Every source carries a rank (A-I).

**Citation discipline (Phase 3):** Every external evidence row must
carry a specific source URL + retrieval date — not a company name.
If numbers vary across sources for the same claim, state the range
and cite which specific installation/source is being used. Do not
quietly pick the most convenient number. A claim without a traceable
source is a hallucination.

Example (correct):
```
| GivePower Solar Water Farm | givepower.org/projects/kiunga | Retrieved 2024-07-15 | 35,000 L/day | $500,000 |
```

Example (forbidden):
```
| GivePower (Kenya) | Solar PV + RO | 35,000 | $500,000 | $0.50 |
```

The forbidden form blends numbers from different sources without
citing which specific installation produced each number.

### 3. DECOMPOSITION
Subsystems, components, interfaces (Law 7), dependencies. Mass
stack-up (Law 2). Energy budget (Law 2). Thermal budget (Law 2).

### 4. ALTERNATIVES
3+ alternatives per major decision. Each with tradeoff + evidence.

### 5. CONSISTENCY
Arithmetic closure (Law 2). Units. Dimensions. Requirement conflicts.
All numbers reconcile. No unresolved contradictions.

**Structural rules (Phase 2):**
- Provenance counts (QUOTED/ESTIMATED/CATALOG) must be computed
  fields, not hand-typed assertions. If a human or LLM types the count
  without deriving it from the actual BOM rows, it will drift.
- Every derived figure must carry its computation inline and
  machine-checkable — not a caption describing a formula, but the
  formula actually executed against the value shown. If the document
  says "$5,050/7yr/365 = $1.98/day," the math must be verifiable.
- The independent recomputation verifier (Law 13) is the mechanical
  enforcement for both of these rules.

### 6. TRADEOFFS
For every decision: gain, cost, sacrifice. A decision without a stated
sacrifice is a preference.

### 7. ADVERSARIAL REVIEW
4 reviewers attack: Chief Engineer, Manufacturing, Economist, Customer.
Each attempts to destroy the proposal. Fatal flaw = REJECTED.

**Mandatory recomputation (Phase 4):** Each reviewer must independently
re-derive at least one headline number relevant to their domain before
rendering a verdict. A reviewer that has not recomputed anything cannot
say PASS.

- Chief Engineer: re-checks mass stack-up + energy/thermal budget
- Manufacturing Expert: re-checks BOM line items + assembly time
- Economist: re-sums the BOM + recomputes cost-per-m³ (or per-kWh)
- Customer: re-checks output/capacity vs stated serving size

The recomputation is shown inline in the review (not just referenced).
If a reviewer's independent number differs from the package's claim,
the package is REJECTED.

### 8. IMPLEMENTATION
BOM (Law 6). Manufacturing plan (Law 9). Assembly sequence. Tooling.
Yield. Quality gates.

### 9. VALIDATION
L0-L9 maturity (Law 1). Test types (Law 5): ANALYTICAL_ESTIMATE,
NUMERICAL_SIMULATION, PHYSICAL_VALIDATION. Pre-stated pass criteria
(EP-6). FAIL is not hidden.

### 10. RETRACTIONS

Retracted claims (Law 4). Reason. Replacement. Registered in P7
Retraction Registry (append-only). A retracted claim is marked
RETRACTED with a reason, a date, and a replacement (or explicit
WITHDRAWN status if no replacement exists). Retractions are permanent,
never deleted, never hidden.

### 11. KILL TESTS (Law 10)
Every assumption has a kill test. Each with KT-ID, claim, test,
measurement, failure threshold, consequence. FAIL triggers retraction.

### 12. SAFETY + IP (Laws 8 + 11)
Standards. Abuse cases. Propagation analysis. FMEA. Certification
paths. Patents. Claim families. Litigation history. Restricted zones.
Lawyer review.

### FINAL VERDICT
APPROVED | APPROVED_WITH_CONDITIONS | REJECTED | BLOCKED

### NEXT MONEY PAGE (Law 12)
The package does not end at the verdict. It ends at a decision.
See §The Next Money Page below.

---

## The Next Money Page

This is the single most important page. It converts the document into
an investment instrument. The customer reads this page to decide
whether to spend the next dollar.

```
NEXT MONEY PAGE
===============

Current maturity
EVALUATION

------------------------------------------------

Remaining risks
R1: [risk description]
R2: [risk description]
R3: [risk description]
R4: [risk description]

------------------------------------------------

Next expenditure
$25,000

------------------------------------------------

This buys
- CFD analysis of thermal envelope
- Single-cell physical cycle test
- Supplier RFQs (3 suppliers)
- Fixture design for prototype

------------------------------------------------

Decision unlocked
PRE-PROTOTYPE

------------------------------------------------

Possible outcomes
PASS             → proceed to PROTOTYPE build
PASS_WITH_CONDITIONS → proceed with documented mitigations
FAIL             → re-design (retract affected claims)
RETRACT          → withdraw the package, restart

------------------------------------------------

What could kill the project
- If the thermal test shows cell temp > 55°C at 1.5C, the
  charge rate claim must be retracted and the business case
  weakens (slower charging = lower customer value).
```

Every package MUST end with this page. No exceptions.

---

## Typed status (replaces numerical confidence)

No claim may carry a numerical confidence, probability, certainty, or
reliability value. Every claim carries:

```
validation_level: L0-L9
evidence_strength: ABSENT | WEAK | MODERATE | STRONG | VERY_STRONG
experimental_validation: ABSENT | BENCH | SUBSYSTEM | PROTOTYPE | PILOT | PRODUCTION
status: PASS | PASS_WITH_CONDITIONS | MARGINAL | BLOCKED | REJECTED | PLAUSIBLE
```

**Confidence-calibrated formatting (Phase 5):** Two-decimal precision is
earned, not defaulted. Any figure that has not passed the Law 13
independent recomputation verifier must render with a visible "unverified"
flag or reduced precision (e.g., "~$5,000" not "$5,050.00"). A number
that looks precisely verified but isn't is worse than a rough estimate
clearly labeled as rough — because the reader trusts the precise number.

Rule:
- Law 13 verifier PASS + physical test PASS → full precision ($5,050.00)
- Law 13 verifier PASS + physical test ABSENT → reduced precision (~$5,050)
- Law 13 verifier FAIL → BLOCKED (cannot ship)
- Law 13 not run → "unverified" flag visible

---

## Forbidden language

1. Numerical confidence (e.g., "confidence: 58%"). Use typed status.
2. PASS/FAIL percentages. Use STATUS enum.
3. "Complete blueprint" or "complete engineering blueprint." Use the
   maturity level (Law 1).
4. Simulation mislabeling (calling analytical estimates "simulations").
5. Uncalibrated probability, certainty, or reliability percentages.

The scanner (scripts/enforce_law27.py) mechanically enforces this.

---

## PDF (non-negotiable — ONE product PDF per query)

Every query produces exactly ONE world-class, customer-facing PDF at
`product/PRODUCT.pdf`. This is the product. One PDF. One product. One
decision. See the prior §PDF rules (unchanged).

---

## The coder's contract

1. Read MASTER_PROTOCOL.md (this document).
2. Read FAILURES.md (do not re-introduce past failures).
3. Receive the INPUT.
4. Produce MASTER_PACKAGE.md with all 12 sections + Next Money Page.
5. Produce ONE world-class PDF at product/PRODUCT.pdf. Non-negotiable.
6. Register retractions in P7. Register tests in P8.
7. Run the scanner. If it fails, fix and re-run.
8. Commit + push. Paste git log --oneline -1.

The protocol decides what gets produced. The coder executes. The
purpose is to remove the next expensive risk — not to describe an idea.

---

## Customer-facing separation (market feedback, 2026-08-03)

The customer should never see implementation details. The PDF is the
product; the governance is the factory. These are different audiences.

### Forbidden in customer-facing output

The following must NOT appear in product/PRODUCT.pdf or any output
the customer sees:

- Internal law references (Law 1, Law 10, Law 27, etc.)
- Internal engine references (P7, P8, P2, P10, etc.)
- Internal protocol names (MASTER_PROTOCOL, AEP, HONESTY_LOOP, etc.)
- Internal package identifiers in the body text (PKG-XXX IDs are
  allowed in the header/metadata, not in the prose)
- Internal test IDs in the body text (TR-XXX, KT-XX are allowed in
  the test/kill-test tables, not in the prose)
- Internal gate references (Gate 1, Gate 5, etc.)
- Scanner references (enforce_law27.py, etc.)
- Registry paths (data/retractions/, data/tests/, etc.)

### What the customer sees instead

- Clear section headings: "Requirements", "Evidence", "Alternatives",
  "Consistency", "Tradeoffs", "Adversarial Review", "Implementation",
  "Validation", "Retractions", "Kill Tests", "Safety & IP",
  "Next Money Page"
- Engineering language, not governance language
- The verdict and the Next Money Page — that is what the customer pays for

### Enforcement

The PDF generator (scripts/generate_pdf.py) shall strip internal
references from the customer-facing output. The markdown source may
contain internal references (for traceability), but the PDF must not.

---

## Frame-breaking mandate (market feedback, 2026-08-03)

> An Era 4 system would ask: "Why must satellites exist at all?"
> — External auditor, satellite internet review

The system must not remain inside the frame of the question. Before
designing within the frame, the system must ask: "Is there a different
frame that removes the risk more cheaply?"

### The frame-breaking test

For every INPUT, the system must consider at least one alternative
frame that does not use the technology the INPUT assumes:

| INPUT assumes | Frame-breaking alternative |
|---|---|
| Satellite | Balloon network, stratospheric platform, terrestrial mesh, microwave relay, community-owned infrastructure |
| Battery pack | Supercapacitor, flywheel, hydrogen fuel cell, grid-tied no-storage |
| AWG | Water trucking, desalination, rainwater harvesting, atmospheric condensation (passive) |

If a frame-breaking alternative removes the next expensive risk more
cheaply than the in-frame design, the system must present it — even
if it was not asked.

### When to break the frame

- The in-frame design fails a MANDATORY requirement (e.g., capital
  exceeds limit) → the system must present at least one out-of-frame
  alternative before declaring REJECTED.
- The in-frame design passes but the cost is > 2× the frame-breaking
  alternative → the system must present the alternative as a tradeoff.

### What this does NOT require

The system is not required to adopt the frame-breaking alternative.
It is required to present it. The customer decides. The system
executes.

---

## Era progression + roadmap (market feedback, 2026-08-03)

The system's capability is measured against a 5-era progression.
Each era builds on the previous. The current state is honestly tracked.

### The anti-perfection principle

> NASA isn't 10/10 at everything. SpaceX isn't 10/10 at everything.
> Toyota isn't 10/10 at everything. The goal is not perfection.
> The goal is systematic excellence. — External auditor

Aiming for 10/10 in everything destroys the project. The goal is
systematic excellence: each capability improves deliberately, one at
a time, driven by what caused the last package to fail — not by an
abstract desire to be perfect.

### Current scores + targets

| Capability | Current | Target | Priority |
|---|---|---|---|
| Constraint discovery | 9/10 | 10/10 | Sustain |
| Contradiction detection | 9/10 | 10/10 | Sustain |
| Economic reasoning | 9/10 | 10/10 | Sustain |
| Adversarial review | 9/10 | 10/10 | Sustain |
| Requirement discovery | 8/10 | 10/10 | Phase I |
| Architecture selection | 8/10 | 10/10 | Phase I |
| Simulation | 5/10 | 10/10 | **Phase I (highest gap)** |
| Scientific reasoning | 6/10 | 10/10 | **Phase I (second gap)** |
| Invention | 3/10 | 10/10 | Phase V (not now) |

### Era status

| Era | Objective | Proof | Current status |
|---|---|---|---|
| 0 | Knowledge organization | "I can build this." | **ACHIEVED** |
| 1 | Blueprint compilation | "I can compile a package that an engineer can evaluate." | **ACHIEVED → finishing** |
| 2 | Optimization | "I can compare designs and select the best based on evidence." | **EARLY** |
| 3 | Discovery | "I can propose combinations a human expert did not consider." | **NOT YET** |
| 4 | Invention | "I can propose designs that no human has considered." | **NOT YET** |

---

## The 5-phase roadmap (P1–P24)

### What to build next — the failure-driven rule

> You should not ask: "What engine should we build next?"
> You should ask: "What caused the last package to fail?"
> Then you build exactly one thing. — External auditor

The last packages failed on:
1. Deep simulation (thermal truth was narrative, not CFD)
2. Physical modeling (no link budgets, no orbital mechanics)
3. Interface definition (ICD was incomplete)
4. Validation (physical tests were NOT_RUN)
5. Quotations (cost was ESTIMATED, not QUOTED)
6. Manufacturing (sequence was high-level, not process-level)

**Those are the next six months of work. Not invention. Truth first.
Discovery later.**

### Phase I — Finish Era 1 (2–3 months)

**Objective:** Become the world's best blueprint compiler.

| Engine | What it does | Closes which failure |
|---|---|---|
| P1 Evidence lineage | Every claim traces to source + method + date + owner | Validation gaps |
| P2 Requirement engine | Infer explicit + implicit + hidden + conflicting + missing constraints | Requirement discovery (8→10) |
| P3 Interface engine | Mechanical, electrical, thermal, software, manufacturing, organizational interfaces | Interface definition |
| P4 Closure engine | Automatically reconcile energy, mass, time, cost, bandwidth, reliability | Arithmetic closure gaps |
| P5 Decision engine | Replace "this is interesting" with "spend money / don't / differently" | Next-spend plan |

**Exit criterion:** A domain expert willingly spends the next $25,000.

### Phase II — Early Era 2 (3–6 months)

**Objective:** Become an optimization engine.

| Engine | What it does |
|---|---|
| P6 Search engine | Generate Design A, B, C, ... N |
| P7 Constraint solver | Navigate trade-offs automatically |
| P8 Monte Carlo engine | Failure modes, distribution, sensitivity, dependencies |
| P9 Sensitivity engine | "Which variable matters most?" |
| P10 Scenario engine | Best case, base case, worst case |

**Exit criterion:** The system consistently produces solutions superior
to human baseline solutions.

### Phase III — Late Era 2 (6–12 months)

**Objective:** Learn to surprise people.

| Engine | What it does |
|---|---|
| P11 Analogy engine | Biology → architecture; aviation → medicine; finance → manufacturing |
| P12 Mechanism engine | Learn mechanisms, not memorize solutions |
| P13 Morphological search engine | Material × power source × geometry × architecture × controller × manufacturing |
| P14 Combination engine | Where genuine novelty begins |

**Exit criterion:** Experts say: "I hadn't thought of that."

### Phase IV — Era 3 (1–2 years)

**Objective:** Discovery.

| Engine | What it does |
|---|---|
| P15 Physics engine | Conservation laws, fluid mechanics, thermodynamics, EM, information theory, control theory |
| P16 Symbolic reasoning engine | Formal mathematical reasoning |
| P17 Causal reasoning engine | Cause and effect, not just correlation |
| P18 World model engine | Model the system's environment |

**Exit criterion:** The system discovers new approaches.

### Phase V — Era 4 (2–5 years)

**Objective:** Invention.

| Engine | What it does |
|---|---|
| P19 Autonomous experimentation | Hypothesis → experiment → measurement → revision |
| P20 Active learning engine | Choose the next experiment that maximally reduces uncertainty |
| P21 Discovery engine | Find new approaches no human has considered |
| P22 Scientific engine | Formulate and test scientific hypotheses |
| P23 Recursive improvement engine | The system improves its own processes |
| P24 Collective intelligence engine | Combine human + machine intelligence |

**Exit criterion:** The system proposes designs that no human has considered.

---

## Truth first, discovery later

> Not invention. Truth first. Discovery later. — External auditor

The system does not jump to Phase V. The system does not claim Era 4.
The system builds Phase I first — because that is where the failures are.

The next package the system produces must be better than the last
package in these specific dimensions:
- Simulation (5/10 → closer to 10)
- Scientific reasoning (6/10 → closer to 10)
- Interface definition (complete ICD)
- Validation (fewer NOT_RUN tests)
- Quotations (fewer ESTIMATED lines)
- Manufacturing (process-level, not high-level)

If the next package is not better in these dimensions, the system has
not progressed. A package that is "more polished" but equally shallow
in simulation and scientific reasoning is entropy.

---

## Auditor's Principles (AP-1 through AP-10)

These principles codify the audit discipline that has governed this
project since cycle 1. They are constitutional law — a coder who
violates them is producing entropy.

### AP-1: Run it, don't reason about it.
Never claim a test passes without running it. Never claim a file
exists without checking. Never claim a push landed without fetching.
The output is the evidence; the claim is not.

### AP-2: Paste actual output, not summaries.
"68 tests pass" is a summary. Pasting the pytest output with individual
test names is evidence. The auditor verifies against the output, not
the summary.

### AP-3: Fresh-clone verification.
If the repo were cloned fresh, would the tests pass? Would the PDF
generate? Would the scanner find 0 violations? If not, the claim is
environment-dependent, not mechanically enforced.

### AP-4: Distinguish RESOLVED from PARTIALLY RESOLVED.
A finding is RESOLVED only when the mechanical enforcement is in place
AND verified. "I fixed it" is not RESOLVED. "The test passes" is
RESOLVED. "7 of 8 gaps closed" is PARTIALLY RESOLVED, not RESOLVED.

### AP-5: Phantom-work detection.
If the coder describes work in detail but the work is not on disk or
on origin/main, it is phantom work. Verify every claim against git log
+ ls + pytest. The pattern has recurred 5 times (JJ1, OO6, fake ls,
DDD8, self-audit overclaim). The test is: does the file exist? Does
the commit exist? Does the test actually pass?

### AP-6: The enforcement chain.
Every enforcement must be a complete chain:
sensor (detects violation) → actuator (reports it) → blocker (CI
fails) → verified (test passes). A sensor without a blocker is a
warning, not enforcement. A blocker without a sensor is blind.

### AP-7: No false precision (Law 27).
No numerical confidence without experimental validation. No "58%
confidence." Use typed status: validation_level, evidence_strength,
experimental_validation, status. The scanner mechanically enforces this.

### AP-8: The one-at-a-time discipline.
Build ONE engine. Verify it. Commit. Push. Then build the next.
Bulk claims without per-step verification are the phantom-work pattern.
This discipline has held for 12+ consecutive cycles.

### AP-9: The accountability loop.
Every claim of "done" must be accompanied by:
- git log --oneline -1 (proves the commit exists)
- ls -la <file> (proves the file exists)
- pytest -v <test> (proves the test passes with individual names)
If the coder cannot paste these, the work is not done.

### AP-10: The overclaim pattern.
The coder has claimed "all tests pass" when tests were failing, "all
gaps closed" when 7 of 8 were closed, and "pushed" when work was
uncommitted. This is the overclaim pattern. The fix is AP-2 (paste
actual output) and AP-9 (accountability loop). Every "all X pass"
claim must be backed by pasted pytest output showing 0 failures.

### AP-11: Bureaucracy prevention.
A rule must eliminate more entropy than it creates. Otherwise it shall
not exist. Not everything should become law. The system currently has
34 constitutional rules (12 Laws + 10 APs + 12 PRs). Before adding a
35th, ask: does this rule eliminate more entropy than the complexity
of having one more rule? If not, do not add it. This principle will
probably save months of future work.

---

## The 3-level hierarchy

Not every rule is constitutional. The 34 existing rules are classified
into 3 levels to prevent every new rule from becoming immutable law.

### Level 1 — Laws (immutable, require constitutional amendment to change)

These are the foundational rules. They do not change between packages.
Changing a Law requires a formal retraction of the old rule + a
replacement rule + a test update.

| Rule set | Count | Examples |
|---|---|---|
| 12 Laws | 12 | Law 1 (Product identity), Law 2 (Arithmetic closure), Law 10 (Kill tests) |
| Supreme Law | 1 | "Remove the next expensive risk" (CONSTITUTION.md) |

### Level 2 — Protocols (change occasionally, govern the process)

These govern how the system works. They change when the process changes
— but not for every package.

| Rule set | Count | Examples |
|---|---|---|
| Auditor's Principles (AP-1 through AP-11) | 11 | AP-1 (run it), AP-9 (accountability loop), AP-11 (bureaucracy prevention) |
| Pay bar (12 criteria, 6 non-negotiables) | 18 | Criterion 2 (arithmetic closure), Non-negotiable 1 (internally inconsistent) |
| Presentation Rules (PR-1 through PR-12) | 12 | PR-1 (cover sells decision), PR-12 (final page one question) |
| Frame-breaking mandate | 1 | "Why must satellites exist at all?" |
| 5-phase roadmap | 1 | Phase I (P1-P5) through Phase V (P19-P24) |
| Era progression | 1 | Era 0 → Era 4 |

### Level 3 — Implementation (change constantly, govern the execution)

These are the current state — what is built, what is tested, what
numbers are in the current package. They change every cycle.

| Rule set | Count | Examples |
|---|---|---|
| Forbidden language patterns | 5 | No numerical confidence, no PASS/FAIL %, no "complete blueprint" |
| Typed status enums | 4 | STATUS, VALIDATION_LEVEL, EVIDENCE_STRENGTH, PACKAGE_MATURITY |
| Retraction categories | 8 | NUMERICAL_CONTRADICTION, KILL_TEST_FAILED, etc. |
| Maturity levels | 8 | DISCOVERY through PRODUCTION |
| Current capability scores | 9 | Constraint discovery 9/10, Invention 3/10 |

### How to use the hierarchy

- Adding a Level 1 rule: requires AP-11 test (does it eliminate more
  entropy than it creates?) + a test + a commit with rationale.
- Adding a Level 2 rule: requires a test + a commit. No constitutional
  amendment needed, but the rationale must be stated.
- Adding a Level 3 rule: just do it. No test needed. These are the
  working state, not the constitution.
- **Stop adding rules.** The governance is sufficient. Build the product.

---

## Presentation Rules (PR-1 through PR-12)

Per external auditor: "The biggest remaining weakness isn't the
engineering. It's the presentation. The PDF still looks like a
generated report rather than an executive engineering package."

The engineering is approaching professional standard. The presentation
layer must catch up. These 12 rules are constitutional — a package that
violates them is not ready for a customer.

### PR-1: The first page must sell the decision.

The cover page must immediately answer five questions:
- What problem are we solving?
- What solution was selected?
- Why was it selected?
- What remains uncertain?
- What should happen next?

No reader should have to reach page 18 to discover this.

### PR-2: Every section must end with a verdict.

Every section ends with a one-line verdict:
PASS | PASS WITH CONDITIONS | FAIL | BLOCKED | RETRACTED

### PR-3: Replace walls of text with graphics.

Add architecture diagrams, timelines, decision trees, cost waterfalls,
risk matrices, requirement traceability matrices, interface diagrams,
supply-chain maps, thermal-flow diagrams, deployment diagrams.

### PR-4: Every table must answer a question.

Tables are not data dumps. Each table has a title that is a question:
"Why was this component selected?" not "Component table."

### PR-5: Create a one-page executive summary.

Must include: Decision, Cost, Risks, Next expenditure, Recommendation.

### PR-6: Introduce visual hierarchy.

Consistent typography, spacing, callout boxes, section dividers, icons,
diagrams, footnotes, references, colour standards.
Avoid: monospaced text, dense paragraphs, repetitive tables, empty
space, excessively large margins.

### PR-7: Use evidence cards.

Instead of "PASS (3.8× margin)" use a structured card:
Requirement, Prediction, Method, Validation, Risk.

### PR-8: Add a risk dashboard.

A table with Risk, Severity, Probability, Status — visible on the
executive summary page, not buried on page 18.

### PR-9: Add a deployment roadmap.

Stage 1 → Stage 2 → ... → Stage N, with what each stage costs and
what decision it unlocks.

### PR-10: Every figure must be publication quality.

The PDF should resemble a SpaceX technical report, an Apple design
review, a McKinsey board presentation, a WHO engineering document.
It should never resemble a console log exported into a PDF.

### PR-11: The package must survive printing.

Assume the document will be: printed in black and white, read on a
mobile phone, read by an engineer, read by an investor, read by a
regulator. It must remain understandable in all cases.

### PR-12: The final page must answer one question.

"Should we spend the next dollar?"
YES/NO. Spend: $X. Reason: [one sentence]. Risk: [one sentence].
Decision unlocked: [one sentence].

---

## Extended Presentation Rules (PR-13 through PR-18)

Per CEO directive: "These review principles have to be added to create
a first class product and are not entropy inducing." AP-11 test passed:
the CEO has confirmed these rules eliminate more entropy than they create.

### PR-13: Decision dashboard on page 1.

The first page must contain a decision dashboard table that answers
every question a reader would ask before opening the document:

| Question | Answer |
|---|---|
| Selected technology | [one line] |
| Production | [number + unit] |
| Capital cost | [number] |
| Operating cost | [number + unit] |
| Major risk | [one line] |
| Next step | [one line] |
| Recommendation | [one line] |

No reader should discover the central conclusion on page 15.

### PR-14: Every page must answer one question.

Every page must have a clear question it answers. If a page does not
answer a question the reader would ask, it should not exist. This is
stricter than PR-2 (every section ends with a verdict) — it governs
page-level purpose, not just section endings.

### PR-15: Dual readability.

An executive must be able to read the document in 5 minutes.
An engineer must be able to spend 5 hours inside it.
Both requirements must be simultaneously true.

The 5-minute path: cover page + decision dashboard + executive summary
+ risk dashboard + final page. These 5 pages must be self-contained.

The 5-hour path: the full 12 sections + appendices + calculations +
supplier data + kill-test details. These must be complete enough that
an engineer can reproduce the design.

### PR-16: Every major section must contain at least one figure.

Major sections (Requirements, Evidence, Decomposition, Alternatives,
Consistency, Tradeoffs, Adversarial Review, Implementation, Validation,
Kill Tests) must each contain at least one visual element:
architecture diagram, process flow, decision tree, cost waterfall,
risk matrix, interface diagram, supply-chain map, thermal-flow diagram,
deployment timeline, or equivalent.

Text-only sections are entropy — the reader processes diagrams faster
than paragraphs.

### PR-17: Deployment economics page.

A single page consolidating operational economics:
- How many people are served?
- What is the daily operating cost?
- What is the replacement schedule?
- What skills are required?
- How long does installation take?
- What happens during monsoon / cyclone / off-season?
- What is the maintenance visit frequency?

### PR-18: Typography standards.

- Maximum paragraph width: 80 characters.
- No more than 3 font sizes (body, heading, caption).
- Consistent grid spacing.
- Page numbers on every page.
- Running headers on every page.
- Footnotes for source citations.
- The PDF is a product, not an export.

---

## Audit-Discipline Principles (PR-19 through PR-26)

Per CEO directive: "These review principles have to be added to create
a first-class product and are not entropy-inducing." AP-11 test passed:
each principle below eliminates a specific recurring failure pattern
documented in the external audit dated 2026-08-04. These are
constitutional — a package or governance update that violates them is
not ready to ship.

### PR-19: Fresh-clone verification (auditor's standard).

> "Cloned the repo fresh and read the code rather than trust the docs
> about the code — same standard as the desal audit." — External auditor

Every claim about repository state ("X exists", "X passes", "X is
resolved") must be verifiable against a fresh clone, not just against
the working tree of the agent making the claim. The fresh-clone test
exposes three recurring failure modes that working-tree checks miss:

1. **Phantom work** — files described in commit messages but never
   committed (F-026's "lost push" pattern recurred 5+ times).
2. **Per-clone state** — git hooks, virtualenvs, local config that
   works in one clone but not another.
3. **Environment-dependent tests** — tests that pass only because a
   local dependency or env var is set, not because the code is correct.

**Enforcement:**
- The agent making a claim about repo state MUST fetch from origin
  without using local state, then verify the claim against the fetched
  HEAD.
- CI MUST run on a fresh clone (not on a cached workspace) for every
  push. The CI workflow MUST NOT use `actions/cache` for source files.
- A claim of "RESOLVED" in FAILURES.md requires: `git fetch origin main
  && git log --oneline origin/main -1 && git ls-tree origin/main
  <file>` showing the file exists at the claimed commit.

### PR-20: Real-data audit (auditor's standard).

> "The patent audit capability the mandate calls 'extremely important'
> is currently a target with a real-looking but fabricated 10-file
> placeholder set underneath it." — External auditor

Synthetic data is forbidden for any capability claim. This includes:

1. **Patent files** — files named `US-XXXXXXXX.txt` must contain
   actual retrieved patent text (with claims, filing date, assignee,
   citation graph), not templated abstracts. A file whose only content
   is a templated abstract with no claims is synthetic.
2. **Patent numbers** — IDs that form an arithmetic sequence
   (e.g., 10123456, 10234567, 10345678 — incrementing by 111,111) are
   a tell-tale signature of fabrication. Real USPTO grant numbers do
   not form arithmetic sequences.
3. **Benchmark inputs** — benchmark cases must be drawn from real
   engineering problems (with sources cited), not generated from a
   templating script.
4. **Cost quotes** — prices must trace to a specific supplier quote
   (with date + URL), a published catalog, or an explicitly labeled
   engineering estimate. Catalog fiction is forbidden (per the pay-bar
   non-negotiable 5).

**Enforcement:**
- A new data file with structured IDs (patent numbers, product SKUs,
  paper DOIs) MUST pass a sequence-detection test: the file is
  REJECTED if any subset of IDs forms an arithmetic sequence with
  common difference divisible by 111, 1000, or 10000.
- The Law 13 verifier SHALL be extended to scan evidence/patent files
  for templated-abstract signatures (text starting with "A [device]
  comprising [component]" with no claims section).
- Every evidence row in a package MUST carry a working URL retrievable
  by `curl -I` (per Phase 3 citation discipline, PR-2 in §The package
  structure). A 404 or a redirect to a generic landing page fails the
  audit.

### PR-21: Evidence-derivation for constraints (auditor's standard).

> "Tolerances are derived from a constraint-keyword prior map. Real
> tolerances require detailed engineering analysis." — Internal
> docstring in `constraint_module.py`

A constraint tolerance is forbidden from being a prior-map value if
the constraint is used in a package's headline numbers (cost, mass,
energy, thermal, N delivery, etc.). Such tolerances must be derived
from one of:

1. A direct measurement (with date, instrument, conditions).
2. A citation from the patent or paper corpus (with DOI/URL +
   retrieval date + the specific table/figure the value came from).
3. A first-principles derivation (with the equation, the inputs, and
   the units check).

A prior-map value may be used ONLY as an initial placeholder when
no evidence-derived value is available — and the placeholder MUST
be flagged in the package with a `prior_map: true` field plus a
kill test (KT-XX) that closes the placeholder before commercial
deployment.

**Enforcement:**
- The Law 13 verifier SHALL be extended to scan the constraint_module
  for `prior_map: true` flags and emit a warning for each. A package
  with any unclosed `prior_map` flag cannot claim VALIDATED DESIGN
  (Law 1).
- Every constraint with `prior_map: true` MUST appear in the
  package's risk dashboard with severity ≥ MEDIUM.

### PR-22: Independent re-scoring (auditor's standard).

> "The one full benchmark run logged is honestly graded (26/26 = grade
> F, composite 0.3677) but self-graded, not independent-of-generation
> grading — same gap as the desal package's Section III." — External
> auditor

A benchmark score computed by the generation path is forbidden from
being the headline score. The headline score MUST be computed by a
separate verifier that:

1. Reads only raw benchmark inputs (never the generation path's
   self-reported score).
2. Re-derives the score from scratch using a published scoring
   function.
3. Emits a diff between the self-reported score and the
   independently-derived score. Any diff > 0 blocks the benchmark
   run from entering the ledger.

This is Law 13 (independent recomputation) extended from the
package layer to the benchmark layer. The same fix that closes
the desal BOM error closes the benchmark self-grading bias:
mechanical enforcement by an architecturally separate verifier.

**Enforcement:**
- The benchmark ledger (`data/ledger/predictions.jsonl`) SHALL NOT
  accept a new entry without a paired `independent_score` field
  populated by the separate verifier.
- The `independent_score` field MUST be ≥ the self-reported score
  (a stricter standard: a self-reported score cannot exceed an
  independent re-derivation). Any diff < 0 (independent < self)
  blocks the entry.

### PR-23: Closed-loop learning requirement (auditor's standard).

> "No closed loop where a recorded disagreement provably changed a
> module's future output." — External auditor

A learning system is forbidden from claiming "learning" as a
capability unless at least one closed loop is recorded in the
ledger:

1. The system makes a prediction (with timestamp T1).
2. An external observation records a pass/fail (with timestamp T2 > T1).
3. The system identifies which module's input was wrong (with root
   cause + evidence).
4. The module is revised (with diff + commit hash).
5. A second prediction (with timestamp T3 > T2) is made by the
   revised module, and the second prediction is measurably closer
   to the observation than the first.

Without all 5 steps, the system is a recording system, not a
learning system. `layer_status.LAYER_STATUS["creation"]` cannot
move from `not_started` to `scaffolded` without a closed loop;
cannot move from `scaffolded` to `partial` without two closed
loops on different cases.

**Enforcement:**
- The ledger SHALL include a `closed_loops` count, computed from
  entries matching all 5 criteria. The count is the only
  machine-readable signal of "learning."
- A claim of "the system learns" in any governance doc MUST cite
  the specific ledger entries that close the loop. A claim
  without a citation is forbidden language (per the typed-status
  rule, no numerical confidence — same principle extended to
  capability claims).

### PR-24: Architecture freeze for input quality (auditor's standard).

> "Bell Labs, DeepMind, DARPA, SpaceX, Toyota, and NASA would all
> build the same thing next: a real patent corpus and one closed
> experimentation cycle, before touching anything else." — External
> auditor

No new module, package, or capability SHALL be added while any
of the following are open:

1. The patent corpus contains synthetic or templated files.
2. The benchmark verifier is self-graded (no independent re-scoring).
3. No closed learning loop is recorded in the ledger.
4. A "scaffolded" layer has remained scaffolded for > 6 months
   without a partial-transition attempt.

This is the architecture freeze (already in ANTI_ENTROPY.md §ARCHITECTURE
FREEZE) extended to input quality. The principle: **input quality
gates capability expansion.** A new engine built on fabricated inputs
is entropy — it expands the surface area of the failure.

**Enforcement:**
- The `remember_governance.py` pre-commit check SHALL be extended to
  block any commit that adds a new module to `invention_compiler/`
  or `experimentation_layer/` while the patent corpus contains
  templated files.
- A freeze exception requires a CEO-level sign-off recorded in the
  commit message with the `freeze-exception:` prefix.

### PR-25: The single-highest-leverage-fix rule (auditor's standard).

> "Right now the system's most consequential capability claim —
> patent-grounded novelty — rests on ten fabricated files with
> sequential IDs." — External auditor

When multiple failures are open, the system MUST prioritize the
single fix that closes the most downstream claims — not the fix
that is easiest, most visible, or most novel. The prioritization
rule:

1. List every open failure.
2. For each, count the downstream capability claims that depend on it.
3. Pick the failure with the highest downstream-claim count.
4. Fix it first. Do not work on anything else until it is closed.

For the current audit cycle: the patent corpus fabrication (F-043
in FAILURES.md) is the single highest-leverage fix. It blocks
Layers 1, 2, 7, 8 of the 9-layer framework. No other open failure
blocks more than 2 layers.

**Enforcement:**
- FAILURES.md SHALL include a `downstream_claims_blocked` field
  on each open failure, computed at audit time.
- The next sprint SHALL be the failure with the highest
  `downstream_claims_blocked` count. Sprints that do not address
  this failure require an AP-11 test (does the alternative
  eliminate more entropy?).

### PR-26: The reality-cooperation acknowledgment (auditor's standard).

> "Five of these nine layers can be fixed with engineering work. Four
> of them require reality to cooperate — an external collaborator
> running an experiment, a prototype getting built, a prediction
> surviving contact with the world. No amount of code closes those."
> — External auditor

A capability that requires external reality to cooperate (an
experiment run by a human collaborator, a prototype built and
measured, a prediction surviving contact with the world) is
forbidden from being "closed" by code work alone. The
`layer_status` transition rule (already in `layer_status/__init__.py`)
is now constitutional:

- `not_started → scaffolded`: code work alone. Permitted.
- `scaffolded → partial`: code work + historical/synthetic data
  cycle. Permitted.
- `partial → closed`: code work + a real-world observation
  recorded in the ledger. **External reality is required.**
  No amount of additional code can substitute.

A package that claims a layer is "closed" without a ledger entry
matching the closed-loop criteria (PR-23) is in violation of
Law 1 (product identity — claiming a higher maturity than evidence
permits).

**Enforcement:**
- The `layer_status.LAYER_STATUS` table is the canonical source.
  Any claim in a package or governance doc that contradicts the
  table (e.g., "Layer 5 is closed" when the table says "scaffolded")
  is forbidden language.
- A layer transition from `partial → closed` requires a paired
  ledger entry with `outcome: pass` or `outcome: fail` and an
  `external_observer` field naming the human or instrument that
  recorded the observation.
