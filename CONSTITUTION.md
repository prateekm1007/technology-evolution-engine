# CONSTITUTION

## Eight Constitutional Laws

### Law 1: Transformation, not object.
### Law 2: Explicit constraint surface.
Required constraints: energy, information, time, material, cost, safety, maintenance, regulation, manufacturing, supply_chain
### Law 3: Everything is represented as nodes and edges. The graph is canonical.
### Law 4: Everything must be decomposable.
Operators: eliminate, substitute, miniaturize, distribute, modularize, software_substitution, change_energy_domain, change_information_domain
### Law 5: Every candidate must survive adversarial attack.
### Law 6: The engine may not explain the future without exposing the assumptions that produced it.
### Law 7: Historical permanence.
No benchmark, prediction, assumption, failure, or outcome may be silently altered.
Enforcement: append-only ledgers, immutable benchmark inputs/outputs, versioned graph migrations, reproducible replay, review/resolution via suffixed files.
### Law 8: Verification Standard.
No "verified" label without a successful prediction, a failed prediction,
and replayable evidence. A system can fail for arbitrary reasons — absence
of an error is not verification. Positive and negative evidence are both
required before any claim may be labeled "verified" rather than
"integrated" or "implemented." See `evidence/reports/verification_report.json`
for the current audit against this standard.

## Agent Roster (FROZEN)
Historian, Naturalist, Oracle, Ecologist, Inventor, Destroyer, Cemetery, Prerequisite Engine, Resurrection Engine, Blueprint Generator, Ledger

## Entropy Prevention
Never create versioned duplicates. Never create _new, _fixed, _final, _latest variants.

## Benchmark Disciplines
### Discipline 1: Immutability
Never modify an existing benchmark. Use _review/_resolution suffixes.
### Discipline 2: Provenance
Every benchmark carries: source, domain, created_at, reviewer, version, assumptions, limitations.
### Discipline 3: Drift Detection
Dedicated monitoring for graph expansion, altered assumptions, score changes, calibration shifts.

## Governing Principle

The system shall prefer an uncomfortable truth to an elegant theory.

## Evidence Standards Addendum

`EVIDENCE_STANDARDS.md` (EP-1 to EP-12) extends Laws 7 and 8 to the
documentation layer. Law 7 forbids silently altering history; EP-3
forbids selecting historical preconditions with outcome knowledge.
Law 8 requires positive and negative evidence before "verified";
EP-1 requires the evidence be attached, EP-5 requires it be graded
independently, EP-4 requires the falsifier be pre-stated.

Enforcement: `EVIDENCE_LOOP.md` defines three checkpoints
(pre-claim, pre-commit, pre-phase). `EVIDENCE_FALSIFIERS.md`
tracks every explanatory claim's falsifier. `FAILURES.md` F-041
records the Phase 13 violations that triggered this addendum.

Violations of EP-1 through EP-12 are now severity-P1 governance
failures, on par with F-005 (ledger corruption) and F-011
(false "verified" stamp). The documentation layer is no longer
exempt from the evidence discipline the code layer must follow.
