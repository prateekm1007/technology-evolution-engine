# TEST_REGISTRY_ENGINE

**Status:** Honesty Loop Priority 8 engine (specification).
**Location:** repo root.
**Phase:** Honesty Loop v1.0 / P8.
**Governance:** Per BLUEPRINT_CONSTITUTION.md Law 27 (no numerical certainty without experimental validation), Law 28d (no "simulation" mislabeling), Law 29 (typed status enums). See HONESTY_LOOP.md.
**Triggered by:** Consolidated review finding — "These are not
simulations. These are engineering estimates. The terminology
should change."

> A test that was never run is not a test. A test that was
> run but not recorded is not a test. A test that was
> recorded but not linked to the claim it validates is
> not a test. The Test Registry is the only place where
> tests are real.
> — Consolidated review, post-BP-2

---

## Purpose

The Test Registry Engine maintains a single, append-only
ledger of every test that has been run against a Blueprint
claim — analytical checks, numerical simulations, and
physical validations. The registry distinguishes the three
types rigorously: an analytical estimate is never labeled
a simulation, and a simulation is never labeled a
measurement (per Law 26).

This is Priority 8 because the EV battery blueprint reported
"18 simulations, 28% pass" — but the "simulations" were
analytical estimates. The terminology was wrong, and the
wrongness was invisible until the audit. The Test Registry
makes the distinction mechanical.

---

## Schema

```typescript
interface TestRecord {
    id: string                                 // TR-XXX, immutable
    testType: "ANALYTICAL_ESTIMATE" | "NUMERICAL_SIMULATION" | "PHYSICAL_VALIDATION"
    testName: string                          // human-readable
    claimId: string                            // CL-XXX — the claim this test validates
    validationLevelTarget: "L2" | "L3" | "L4" | "L5" | "L6" | "L7" | "L8" | "L9"
    method: {
        analyticalModel?: string              // the equation/derivation, if ANALYTICAL_ESTIMATE
        numericalModel?: {
            solver: string                   // "FEA (ANSYS)", "CFD (OpenFOAM)", "circuit (LTSpice)"
            meshResolution?: string           // element count or size
            timeStep?: string
            boundaryConditions: string
            modelFile: string                // path to the model file
            runCommand: string               // exact command to reproduce
        }
        physicalTest?: {
            testStand: string                // "bench rig B-001", "vehicle V-001"
            sampleSize: number               // how many units tested
            testDuration?: string            // "500 hours", "1000 cycles"
            measurementInstruments: string[] // calibrated instruments used
            calibrationDate: string          // ISO 8601
            procedureDocument: string        // path to test procedure
        }
    }
    result: {
        status: "PASS" | "PASS_WITH_CONDITIONS" | "MARGINAL" | "FAIL" | "BLOCKED" | "NOT_RUN"
        measuredValue?: string                // what was measured, with units
        expectedValue: string                 // what was expected
        passCriteria: string                  // the pre-stated pass criterion
        dateRun?: string                     // ISO 8601 — when the test was run (null if not yet run)
        runBy?: string                       // who ran it
        rawDataPath?: string                  // path to raw data
        analysisPath?: string                // path to analysis script
    }
    evidenceId: string                        // EV-XXX (P1) — the evidence produced by this test
    retractionId?: string                     // if the test result is retracted (P7)
    status: "PASS" | "PASS_WITH_CONDITIONS" | "MARGINAL" | "BLOCKED" | "REJECTED"
    immutable: true                           // records cannot be edited; supersession requires a new TR
}
```

---

## Test type definitions

### ANALYTICAL_ESTIMATE

A derivation from first principles. No numerical solver,
no physical test. The output is a number computed by
hand-calculus or spreadsheet.

Example: "Pack energy = (cell energy) × (cell count) ×
(pack overhead factor) = 280 Ah × 3.2 V × 96 × 0.93 =
80.2 kWh."

Permitted validation level targets: L2.

### NUMERICAL_SIMULATION

A numerical solver applied to governing equations.
FEA, CFD, circuit simulation, multi-body dynamics.
The output is a number computed by a computer solving
physical equations.

Example: "Thermal CFD: 4.8°C cell-to-coolant ΔT at 2C
discharge, 25°C ambient, 4 L/min glycol flow."

Permitted validation level targets: L3.

### PHYSICAL_VALIDATION

A physical test on a real unit. Bench test, subsystem
test, prototype test, pilot deployment, production
validation. The output is a measured value from a
calibrated instrument.

Example: "Single-cell 2C cycle test: 3500 cycles to
80% DoD, measured on Arbin LBT21084, calibrated
2024-06-15."

Permitted validation level targets: L4-L9 (depending
on test scale).

---

## Registry rules

1. **The registry is append-only.** A test record, once
   written, cannot be edited. If a test is re-run with
   different parameters or on a different unit, a new
   TR-XXX is created. The old TR is marked SUPERSEDED
   with a reference to the new TR.

2. **Test type cannot be relabeled.** A test recorded as
   ANALYTICAL_ESTIMATE cannot later be "promoted" to
   NUMERICAL_SIMULATION by editing. A new TR must be
   created with the new type, and the old TR is
   SUPERSEDED.

3. **Pre-stated pass criteria are mandatory.** A test
   without `passCriteria` written BEFORE the test runs
   violates EP-6 (thresholds committed before the test).
   The registry requires `passCriteria` at registration;
   the test result is filled in after the run.

4. **NOT_RUN tests are valid records.** A test that has
   been planned but not yet run is recorded with
   `status: NOT_RUN`. This makes the test plan visible
   and prevents the "we forgot to test that" failure.

5. **FAIL is a valid result.** A test with `status: FAIL`
   is not hidden. Per Law 4 (failure is an asset) and
   the consolidated review's praise of the kill-test
   engine: a FAIL is recorded, the affected claim is
   retracted (P7), and the test remains in the registry.

6. **Every test links to evidence.** The test produces
   an EV-XXX in the Evidence Lineage (P1). The evidence
   inherits the test's rank: PHYSICAL_VALIDATION →
   rank A or B, NUMERICAL_SIMULATION → rank A, 
   ANALYTICAL_ESTIMATE → rank D (first-principles derivation).

---

## Example test record

```
TR-007:

  testType: PHYSICAL_VALIDATION
  testName: "Single-cell 2C fast-charge cycle test"

  claimId: CL-022 ("2C fast charge: 80% in 18 minutes")

  validationLevelTarget: L4

  method:
    physicalTest:
      testStand: "Arbin LBT21084, bench rig B-001"
      sampleSize: 3
      testDuration: "1000 cycles or 80% DoD, whichever first"
      measurementInstruments: ["Arbin LBT21084", "Fluke 87V multimeter", "Type-K thermocouple ×4"]
      calibrationDate: 2024-06-15
      procedureDocument: "tests/procedures/single-cell-2C-charge.md"

  result:
    status: FAIL
    measuredValue: "78% in 18 min, 84% in 24 min (avg of 3 cells);
                    cell surface temp peaked at 62°C (limit: 55°C)"
    expectedValue: "80% in 18 min, surface temp < 55°C"
    passCriteria: "≥80% SoC in 18 min AND surface temp < 55°C"
                  (pre-stated 2024-07-01, before test ran)
    dateRun: 2024-08-01T14:00:00Z
    runBy: "Test Engineer J. Park"
    rawDataPath: "tests/data/2C-charge-2024-08-01.csv"
    analysisPath: "tests/analysis/analyze_2C_charge.py"

  evidenceId: EV-407 (rank A — physical measurement)
  retractionId: RT-005 (claim CL-022 retracted; 2C fast-charge limit reduced to 1.5C)
  status: PASS  (the test itself passed — it ran and produced valid data; the claim failed)

  immutable: true
```

Note the distinction: the TEST status is PASS (it ran
correctly, produced valid data, the pre-stated criteria
were applied honestly). The CLAIM status is FAIL (the
criteria were not met). The Test Registry records the
test; the Retraction Registry (P7) records the claim's
retraction.

---

## What this engine does NOT do

- It does not run tests. Test execution is upstream.
- It does not interpret results. Interpretation is upstream;
  the registry records the measured value and the pre-stated
  pass criteria.
- It does not compute pass/fail. Pass/fail is determined by
  the pre-stated criteria against the measured value; the
  registry records the result.

---

## Pre-stated falsifier (EP-4)

**Claim:** Every test claimed in a Blueprint can be resolved
to a Test Registry entry with type, method, result, and
evidence lineage.

**Falsifier:** A blueprint that reports "18 tests, 28% pass"
but the Test Registry contains fewer than 18 entries — i.e.,
some tests were claimed but never registered. Such claims are
forbidden; the blueprint cannot ship.

**Status:** PENDING. Engine specified; implementation awaits
AEP Gate 1 for the engine itself.
