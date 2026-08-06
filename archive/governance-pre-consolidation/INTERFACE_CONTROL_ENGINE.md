# INTERFACE_CONTROL_ENGINE

**Status:** Honesty Loop Priority 3 engine (specification).
**Location:** repo root.
**Phase:** Honesty Loop v1.0 / P3.
**Governance:** Per BLUEPRINT_CONSTITUTION.md Law 27 (no numerical certainty), Law 28 (forbidden language), Law 29 (typed status enums). See HONESTY_LOOP.md.
**Triggered by:** Consolidated review finding — "You have
components. You do not yet have interfaces."

> A component is an island. An interface is the bridge.
> A blueprint of islands is not a blueprint — it is a parts list.
> — Consolidated review, post-BP-2

---

## Purpose

The Interface Control Engine requires every pair of adjacent
components in a Blueprint to declare the six interface types
that mediate their interaction. Components without declared
interfaces are islands; blueprints of islands are parts lists,
not designs.

This is Priority 3 because the EV battery blueprint failed
auditing on exactly this: it had CTP architecture and module
replacement without reconciling the manufacturing interface
between cell and pack. The contradiction was invisible because
no interface was declared.

---

## The six interface types

Every adjacent component pair must declare ALL SIX interface
types. An "interface" is the contract between two components
that specifies how they interact across a physical, electrical,
thermal, mechanical, communications, manufacturing, or service
boundary.

```text
1. electrical interface      — voltage, current, impedance, connector
2. thermal interface         — heat flow, contact area, thermal resistance, coolant
3. mechanical interface      — fasteners, loads, vibrations, degrees of freedom
4. communications interface  — protocol, bus, addressing, error detection
5. manufacturing interface   — assembly sequence, tolerances, tooling, fixturing
6. service interface         — disassembly sequence, diagnostic access, spare parts
```

A component pair missing any of the six has an undeclared
interface — and an undeclared interface is a future field failure.

---

## Schema

```typescript
interface InterfacePair {
    id: string                              // IF-XXX
    componentAId: string                    // CMP-XXX (the upstream component)
    componentBId: string                    // CMP-XXX (the downstream component)
    pairName: string                        // human-readable label
    interfaces: {
        electrical?: ElectricalInterface
        thermal?: ThermalInterface
        mechanical?: MechanicalInterface
        communications?: CommunicationsInterface
        manufacturing?: ManufacturingInterface
        service?: ServiceInterface
    }
    status: "PASS" | "PASS_WITH_CONDITIONS" | "MARGINAL" | "BLOCKED" | "REJECTED"
    evidenceLineageIds: string[]            // EV-XXX (P1)
    contradictionId?: string                 // if this interface pair contradicts another (P6)
}

interface ElectricalInterface {
    voltageV: number
    currentA: number
    impedanceOhm?: number
    connectorType: string                   // e.g. "Molex MX150", "busbar welded", "wire 4 AWG"
    pinout?: string                          // reference to datasheet
    evidenceId: string
}

interface ThermalInterface {
    heatFlowW: number                       // watts transferred across the interface
    contactAreaM2: number
    thermalResistanceKW: number             // K/W
    coolantMedium?: "air" | "glycol" | "refrigerant" | "phase_change" | "none"
    flowRateLMin?: number
    evidenceId: string
}

interface MechanicalInterface {
    fastenerType: string                    // "M8 bolt", "weld", "adhesive", "press-fit"
    fastenerCount: number
    loadN: number                            // static + dynamic load across interface
    vibrationMode?: string                  // "stiff", "compliant", "isolated"
    degreesOfFreedom: string                // "fixed" | "1-DOF slide" | "free"
    evidenceId: string
}

interface CommunicationsInterface {
    protocol: string                        // "CAN-FD", "I2C", "LIN", "isolated RS-485"
    baudRate?: number
    addressing?: string
    errorDetection: "parity" | "CRC-8" | "CRC-16" | "CRC-32" | "none"
    evidenceId: string
}

interface ManufacturingInterface {
    assemblySequence: string                // step in the manufacturing plan
    toleranceMM: number                      // tolerance stack-up across the interface
    toolingRequired: string                  // "torque wrench 25 Nm", "welder", "press"
    fixturing: string                        // how the parts are held during assembly
    evidenceId: string
}

interface ServiceInterface {
    disassemblySequence: string             // step in the service manual
    diagnosticAccess: "none" | "visual" | "BMS read" | "external probe"
    sparePartAvailable: "yes" | "no" | "made_to_order"
    serviceTimeMin: number                   // minutes to R&R the interface
    evidenceId: string
}
```

---

## Interface rules

1. **Every adjacent pair declares all six interfaces.** An
   interface may be `null` only if the component pair genuinely
   does not interact across that dimension (e.g., two cells in
   the same pack have no communications interface). A `null`
   interface must include a `rationale` field explaining why.

2. **Every interface carries an evidence ID.** An interface
   with no upstream evidence is a guess. The interface must be
   marked `STATUS: BLOCKED` until evidence is supplied.

3. **Contradictions are flagged.** If the manufacturing
   interface says "welded, non-serviceable" but the service
   interface says "field-replaceable, 30-minute R&R," the
   pair is marked `STATUS: REJECTED` and a contradiction is
   registered with P6 (Requirement Reconciliation).

4. **CTP vs. module-replacement is the canonical contradiction.**
   A Cell-To-Pack architecture has a manufacturing interface
   of "welded directly to pack busbar (no module housing)."
   A module-replacement architecture has a manufacturing
   interface of "bolted to module busbar, module bolted to
   pack busbar." A blueprint that declares CTP AND
   module-replacement has a contradiction at the
   manufacturing/service interface — and the engine must
   reject it.

5. **Service interface time must be honest.** A service time
   of "5 minutes" on an interface that requires pack removal
   is dishonest. The service time must include all upstream
   disassembly steps.

---

## Example interface pair

```
IF-014: cell-to-busbar interface (96 cell-busbar joints per pack)

  electrical:
    voltageV: 3.2
    currentA: 250 (peak), 75 (continuous)
    connectorType: "laser-welded busbar, 0.4mm thick"
    evidenceId: EV-201

  thermal:
    heatFlowW: 8.5 (per cell, peak)
    contactAreaM2: 0.0012
    thermalResistanceKW: 0.45
    coolantMedium: "glycol 50%"
    flowRateLMin: 4.0
    evidenceId: EV-202

  mechanical:
    fastenerType: "laser weld"
    fastenerCount: 1
    loadN: 0 (no mechanical load — pack-level housing carries load)
    vibrationMode: "stiff"
    degreesOfFreedom: "fixed"
    evidenceId: EV-203

  communications: null
    rationale: "Cell-to-busbar is a power interface only; cell
                communications go through the BMS harness (IF-022)."

  manufacturing:
    assemblySequence: "step 7 — laser weld cell tabs to busbar"
    toleranceMM: 0.2
    toolingRequired: "laser welder, 1000W, fixture PAL-001"
    fixturing: "PAL-001 pallet, 96-cell nest"
    evidenceId: EV-204

  service:
    disassemblySequence: "N/A — laser welds are non-serviceable;
                          cell replacement requires pack teardown
                          (8 hours, factory return)"
    diagnosticAccess: "BMS read (cell voltage, 1Hz)"
    sparePartAvailable: "no"
    serviceTimeMin: 480
    evidenceId: EV-205

  status: PASS_WITH_CONDITIONS
    (condition: service interface is REJECTED by Law 19 if field
     replacement is a stated requirement; see contradiction IF-014
     vs requirement R-008 in REQUIREMENT_RECONCILIATION_ENGINE)
```

---

## What this engine does NOT do

- It does not design interfaces. Design is upstream.
- It does not simulate interface behavior. That is the
  SIMULATION_ENGINE's job.
- It does not enforce interfaces. Enforcement is at the
  blueprint level — the engine produces the contract; the
  Honesty Loop's Gate 11 (Loop Closure) checks the contract
  exists.

---

## Pre-stated falsifier (EP-4)

**Claim:** Every adjacent component pair in a Blueprint can
declare all six interface types.

**Falsifier:** A component pair where one or more interfaces
cannot be declared because the design has not specified how
the components interact across that dimension. Such pairs
must be marked `STATUS: BLOCKED` — the Blueprint may not
ship with undeclared interfaces.

**Status:** PENDING. Engine specified; implementation awaits
AEP Gate 1 for the engine itself.
