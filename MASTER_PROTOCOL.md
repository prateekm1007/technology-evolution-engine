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

### 3. DECOMPOSITION
Subsystems, components, interfaces (Law 7), dependencies. Mass
stack-up (Law 2). Energy budget (Law 2). Thermal budget (Law 2).

### 4. ALTERNATIVES
3+ alternatives per major decision. Each with tradeoff + evidence.

### 5. CONSISTENCY
Arithmetic closure (Law 2). Units. Dimensions. Requirement conflicts.
All numbers reconcile. No unresolved contradictions.

### 6. TRADEOFFS
For every decision: gain, cost, sacrifice. A decision without a stated
sacrifice is a preference.

### 7. ADVERSARIAL REVIEW
4 reviewers attack: Chief Engineer, Manufacturing, Economist, Customer.
Each attempts to destroy the proposal. Fatal flaw = REJECTED.

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
