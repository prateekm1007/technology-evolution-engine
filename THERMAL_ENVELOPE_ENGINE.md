# THERMAL_ENVELOPE_ENGINE

**Status:** Honesty Loop Priority 10 engine (specification).
**Location:** repo root.
**Phase:** Honesty Loop v1.0 / P10.
**Governance:** Per BLUEPRINT_CONSTITUTION.md Law 27 (no numerical certainty without experimental validation), Law 28 (forbidden language), Law 29 (typed status enums). See HONESTY_LOOP.md.
**Triggered by:** Consolidated review finding — the EV battery
blueprint's kill test FAILED on 2C fast charge (cell surface
temp peaked at 62°C, limit was 55°C). The thermal envelope was
never specified as a first-class object.

> A thermal envelope is not a temperature. It is a contract:
> the assembly operates correctly within this envelope, fails
> outside it. A blueprint without a thermal envelope is a
> blueprint that does not know when it stops working.
> — Consolidated review, post-BP-2

---

## Purpose

The Thermal Envelope Engine requires every Blueprint that
handles heat (generation, transfer, storage, or rejection)
to declare an explicit thermal envelope: operating range,
heat generation, heat rejection, ambient assumptions, and
failure thresholds. Thermal claims without envelopes are
forbidden.

This is Priority 10 because the 2C fast-charge kill test
failure was the single most important finding of the EV
battery audit. The thermal limit was 55°C; the cells hit
62°C; the system reported FAIL honestly. But the envelope
was never declared — the failure was detected at kill-test,
not at design time. The Thermal Envelope Engine makes the
envelope explicit at design time so failures are detected
earlier.

---

## Schema

```typescript
interface ThermalEnvelope {
    id: string                                 // TE-XXX
    assemblyId: string                        // PACK-XXX, ROBOT-XXX, etc.
    operatingRange: {
        storageMinC: number
        storageMaxC: number
        operatingMinC: number
        operatingMaxC: number
        survivalMinC: number                  // survives but does not operate
        survivalMaxC: number
        evidenceId: string                     // EV-XXX (P1)
    }
    heatGeneration: HeatSource[]
    heatRejection: HeatSink[]
    ambientAssumption: {
        ambientC: number                      // design-point ambient temperature
        ambientRangeC: [number, number]       // range of ambients the design assumes
        coolantInletC?: number                // coolant inlet temperature, if liquid-cooled
        airflowMS?: number                    // airflow in m/s, if air-cooled
        evidenceId: string
    }
    failureThresholds: {
        cellSurfaceMaxC: number                // hard limit; exceeding = thermal runaway risk
        busbarMaxC: number
        coolantOutletMaxC: number
        thermalRunawayTriggerC: number         // the point of no return
        evidenceId: string
    }
    steadyStateAnalysis?: SteadyStateRecord   // at design-point ambient, continuous operation
    transientAnalysis?: TransientRecord       // at design-point, peak load (e.g. 2C fast charge)
    status: "PASS" | "PASS_WITH_CONDITIONS" | "MARGINAL" | "BLOCKED" | "REJECTED"
    evidenceLineageIds: string[]
    retractionId?: string                      // if a prior thermal claim is retracted (P7)
}

interface HeatSource {
    componentId: string                       // CMP-XXX
    heatGenerationW: number                   // watts, at design-point load
    heatGenerationPeakW: number               // watts, at peak load (e.g. 2C fast charge)
    surfaceAreaM2: number                     // heat exchange surface
    evidenceId: string
    testRegistryId?: string                  // TR-XXX (P8) — physical measurement, if L4+
}

interface HeatSink {
    sinkType: "LIQUID_COOLANT" | "AIR_FORCED" | "AIR_NATURAL" | "PHASE_CHANGE" | "STRUCTURAL"
    componentCooledId: string                 // CMP-XXX
    heatRemovalCapacityW: number              // watts, at design-point
    evidenceId: string
    testRegistryId?: string                  // TR-XXX — physical measurement
}

interface SteadyStateRecord {
    method: "ANALYTICAL_ESTIMATE" | "NUMERICAL_SIMULATION" | "PHYSICAL_VALIDATION"
    ambientC: number
    loadDescription: string                   // "1C continuous discharge"
    cellMaxC: number                          // predicted or measured
    cellMinC: number
    deltaCellCoolantC: number                 // cell-to-coolant ΔT
    evidenceId: string
    testRegistryId?: string
}

interface TransientRecord {
    method: "ANALYTICAL_ESTIMATE" | "NUMERICAL_SIMULATION" | "PHYSICAL_VALIDATION"
    scenario: string                          // "2C fast charge, 0%→80% SoC, 18 min"
    durationMin: number
    cellMaxC: number                          // peak temperature during transient
    cellSurfaceMaxC: number                   // peak surface temperature
    marginToFailureC: number                  // failureThresholds.cellSurfaceMaxC - cellSurfaceMaxC
    status: "PASS" | "PASS_WITH_CONDITIONS" | "MARGINAL" | "FAIL"
    evidenceId: string
    testRegistryId?: string
}
```

---

## Envelope rules

1. **Every thermal claim has an envelope.** A claim like
   "cell surface temp 48°C at 1C" is forbidden unless the
   envelope (ambient, coolant inlet, airflow, load, duration)
   is declared. A temperature without an envelope is a
   number without context.

2. **Heat generation must equal heat rejection at steady
   state.** The engine sums `heatGenerationW` and compares
   to `heatRejectionW`. If generation > rejection, the
   assembly is in thermal runaway — `STATUS: REJECTED`.

3. **Failure thresholds must be declared at design time.**
   A failure threshold discovered at kill-test (e.g., the
   55°C cell-surface limit) must already be in the envelope.
   Discovering the threshold at kill-test is acceptable;
   not having it at design time is not.

4. **Transient analysis is required for peak-load scenarios.**
   A steady-state analysis is insufficient if the assembly
   has peak loads (fast charge, regen, fault conditions).
   The transient record declares the peak temperature and
   the margin to failure.

5. **Margins are explicit.** `marginToFailureC` is required
   in transient records. A margin of 0°C (the assembly
   hits the limit exactly) is `STATUS: MARGINAL`. A
   negative margin (the assembly exceeds the limit) is
   `STATUS: FAIL` and triggers a retraction (P7).

6. **Coolant inlet temperature is part of the envelope.**
   "Cells at 48°C" means nothing without "coolant at
   25°C, 4 L/min, glycol 50%." The envelope declares the
   coolant inlet temperature and flow rate.

---

## Canonical example: the 2C fast-charge failure

```
TE-001: 75 kWh LFP pack, thermal envelope

  operatingRange:
    storageMinC: -20
    storageMaxC:  45
    operatingMinC: -10
    operatingMaxC:  50
    survivalMinC: -30
    survivalMaxC:  60
    evidenceId: EV-601

  heatGeneration:
    - componentId: CMP-006 (cells)
      heatGenerationW: 1200  (1C continuous)
      heatGenerationPeakW: 3600  (2C fast charge)
      surfaceAreaM2: 14.4
      evidenceId: EV-602
      testRegistryId: TR-007  (2C cycle test, measured)

  heatRejection:
    - sinkType: LIQUID_COOLANT
      componentCooledId: CMP-006
      heatRemovalCapacityW: 1800  (1C continuous, steady state)
      evidenceId: EV-603
      testRegistryId: TR-004  (coolant flow test)

  ambientAssumption:
    ambientC: 25
    ambientRangeC: [20, 40]
    coolantInletC: 25
    evidenceId: EV-604

  failureThresholds:
    cellSurfaceMaxC: 55
    busbarMaxC: 90
    coolantOutletMaxC: 45
    thermalRunawayTriggerC: 80
    evidenceId: EV-605

  steadyStateAnalysis:
    method: NUMERICAL_SIMULATION  (CFD, OpenFOAM)
    ambientC: 25
    loadDescription: "1C continuous discharge"
    cellMaxC: 35.2
    cellMinC: 33.8
    deltaCellCoolantC: 10.2
    evidenceId: EV-606
    testRegistryId: TR-005

  transientAnalysis:
    method: PHYSICAL_VALIDATION  (single-cell, 3 samples)
    scenario: "2C fast charge, 0%→80% SoC, 18 min"
    durationMin: 18
    cellMaxC: 62.4  (predicted: 58.1°C, measured: 62.4°C — measured exceeded predicted)
    cellSurfaceMaxC: 62.4
    marginToFailureC: 55 - 62.4 = -7.4  (NEGATIVE MARGIN — assembly exceeds limit)
    status: FAIL
    evidenceId: EV-407  (TR-007)
    testRegistryId: TR-007

  status: REJECTED
    (failure: 2C fast-charge transient exceeds cell surface limit by 7.4°C.
     Affected claim CL-022 ("2C fast charge: 80% in 18 min") retracted;
     see RT-005. Replacement: 1.5C max charge rate; thermal envelope
     relaxed to allow 1.5C continuous. See DESIGN_CHANGE_LOG.)
```

This is exactly the failure the kill-test caught — but now
it is declared at design time, not discovered at kill-test.
The blueprint cannot ship with `STATUS: REJECTED` thermal
envelope; the design must be revised (reduced charge rate,
better coolant flow, larger heat sinks) until the envelope
passes.

---

## What this engine does NOT do

- It does not solve the heat equation. That is the
  simulation engine's job (or a physical test).
- It does not design cooling systems. Design is upstream.
- It does not set failure thresholds. Thresholds come from
  cell datasheets, regulations, and physics. The engine
  records them and checks that the design respects them.

---

## Pre-stated falsifier (EP-4)

**Claim:** Every thermal claim in a Blueprint can be replaced
by an explicit thermal envelope with operating range, heat
generation, heat rejection, ambient assumptions, and failure
thresholds.

**Falsifier:** A thermal claim where the envelope cannot be
constructed — i.e., the operating range is unknown, the heat
generation is unmeasured, or the failure threshold is
undeclared. Such claims must be `STATUS: BLOCKED`; the
package cannot ship.

**Status:** PENDING. Engine specified; implementation awaits
AEP Gate 1 for the engine itself.
