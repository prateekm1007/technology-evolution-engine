# MANUFACTURING_ENGINE

**Status:** Phase 16A Deliverable 8.
**Location:** repo root.
**Phase:** 16A.

---

## Purpose

The Manufacturing Engine produces the manufacturing plan for an
idea: what materials are needed, who supplies them, how the
assembly works, and what tolerances are required.

---

## Schema

```typescript
interface ManufacturingPlan {
    materials: string[]
    suppliers: string[]
    assemblySteps: string[]
    tolerances: string[]
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `materials` | string[] | yes | The raw materials and sub-components needed. References components from COMPONENT_ENGINE.md. |
| `suppliers` | string[] | yes | The supplier names or categories. "Sole-source" flags single-supplier risk. |
| `assemblySteps` | string[] | yes | The ordered assembly process. Each step is a discrete manufacturing operation. |
| `tolerances` | string[] | yes | The manufacturing tolerances required. "Tight" flags precision requirements that may limit supplier options. |

---

## Example

### Autonomous farming robot

```json
{
  "materials": [
    "Aluminum chassis extrusions",
    "Steel frame members",
    "Li-ion battery cells (18650 format)",
    "Solar panels (monocrystalline, 400W)",
    "Electric motors (brushless DC, 1kW)",
    "GPS module (RTK, centimeter accuracy)",
    "Camera modules (stereo, global shutter)",
    "Processor board (ARM-based, edge AI)",
    "Sensor suite (temperature, humidity, soil moisture, NDVI)",
    "Communication module (4G/LTE + LoRaWAN)"
  ],
  "suppliers": [
    "Battery cells: multi-source (Panasonic, LG Chem, Samsung SDI)",
    "Solar panels: multi-source (First Solar, Jinko, Trina)",
    "GPS modules: sole-source (Trimble or u-blox)",
    "Processor: multi-source (NXP, NVIDIA, Qualcomm)",
    "Camera modules: multi-source (Sony, OmniVision)",
    "Chassis materials: multi-source (local aluminum extrusion)"
  ],
  "assemblySteps": [
    "1. Chassis welding and frame assembly",
    "2. Battery pack assembly and integration",
    "3. Solar panel mounting and wiring",
    "4. Motor installation and drivetrain connection",
    "5. Electronics bay installation (processor, GPS, comms)",
    "6. Sensor suite installation",
    "7. Software loading and calibration",
    "8. Field testing and quality assurance"
  ],
  "tolerances": [
    "Chassis alignment: ±2mm (standard agricultural equipment tolerance)",
    "Battery pack sealing: IP67 (dust and water resistant for field use)",
    "GPS antenna positioning: ±5mm (for RTK accuracy)",
    "Camera alignment: ±1° (for stereo vision)",
    "Motor shaft alignment: ±0.5° (for drivetrain efficiency)"
  ]
}
```

---

## Manufacturing analysis protocol

1. **Bill of materials.** List every material and sub-component (from COMPONENT_ENGINE.md).
2. **Supplier identification.** For each material, identify suppliers. Flag sole-source items as supply-chain risks.
3. **Assembly process.** Define the ordered steps. Each step must be a discrete operation that can be performed by a person or machine.
4. **Tolerance specification.** For each dimension that affects performance, specify the required tolerance. Flag tight tolerances that may limit supplier options.
5. **Yield estimation.** Based on tolerance complexity, estimate manufacturing yield. Low yield (< 90%) is a MANUFACTURING constraint.

---

## Relationship to constraint engine

The Manufacturing Engine feeds the Constraint Engine:

- Sole-source suppliers → MANUFACTURING constraint (severity based on supplier criticality).
- Tight tolerances → MANUFACTURING constraint (severity based on tolerance difficulty).
- Low yield → MANUFACTURING constraint (severity based on yield gap).
- Immature manufacturing process → MANUFACTURING constraint (severity 1.0 if process is at TRL < 7).

---

## Relationship to frozen formula

The frozen formula does not use manufacturing_state directly. The
Phase 12 ablation removed cost_bonus (which was correlated with
manufacturing progress). The Manufacturing Engine is a new
component that addresses Pattern 1 (scaling events) and Pattern 4
(post-maturity exploitation) from BOUNDARY_REGISTRY.md.

---

## What this engine does NOT do

- It does not optimize the manufacturing process. It plans it.
- It does not negotiate with suppliers. It identifies them.
- It does not guarantee quality. It specifies tolerances.
- It does not modify the frozen formula.

---

## Pre-stated falsifier (EP-4)

**Claim:** The 4-field ManufacturingPlan captures all manufacturing information needed to evaluate an idea's producibility.

**Falsifier:** A manufacturing plan that cannot be expressed in this schema — e.g., a plan that requires modeling tooling depreciation, factory layout, or worker training schedules.

**Status:** PENDING. No manufacturing plans have been built (no implementation).
