# MATERIAL_LIBRARY

**Status:** Phase 17 Deliverable 3.
**Location:** repo root.
**Phase:** 17.

---

## Purpose

The Material Library catalogues the physical materials used in
agricultural robot components. Each material has mechanical,
thermal, and cost properties. This library feeds the Component
Library (material IDs) and the CAD Specification (material
selection for parts).

---

## Schema

```typescript
interface Material {
    id: string
    name: string
    category: string          // "metal", "polymer", "composite", "semiconductor", "electrode"
    density_kg_m3: number
    tensileStrength_MPa: number
    thermalConductivity_W_mK: number
    cost_USD_kg: number
    supplier: string         // supplier ID from SUPPLIER_LIBRARY.md
    notes: string
}
```

---

## Material catalog

### MAT-001: Aluminum (6061-T6)

| Field | Value |
|---|---|
| id | MAT-001 |
| name | Aluminum (6061-T6) |
| category | metal |
| density_kg_m3 | 2700 |
| tensileStrength_MPa | 310 |
| thermalConductivity_W_mK | 167 |
| cost_USD_kg | 4.50 |
| supplier | SPL-014 |
| notes | Structural alloy for chassis, housings, frames. Good strength-to-weight ratio. Corrosion-resistant. Weldable. Machinable. Used in 70% of agricultural robot structural components by weight. |

### MAT-002: Silicon (monocrystalline)

| Field | Value |
|---|---|
| id | MAT-002 |
| name | Silicon (monocrystalline) |
| category | semiconductor |
| density_kg_m3 | 2329 |
| tensileStrength_MPa | 7000 (theoretical; practical ~120) |
| thermalConductivity_W_mK | 149 |
| cost_USD_kg | 50 (wafer-grade) |
| supplier | SPL-015 |
| notes | Semiconductor material for processors, sensors, solar cells, GPS modules. Not used structurally. Cost is for wafer-grade, not raw silicon. |

### MAT-003: Copper (C11000 electrolytic tough pitch)

| Field | Value |
|---|---|
| id | MAT-003 |
| name | Copper (C11000) |
| category | metal |
| density_kg_m3 | 8960 |
| tensileStrength_MPa | 220 |
| thermalConductivity_W_mK | 391 |
| cost_USD_kg | 9.00 |
| supplier | SPL-016 |
| notes | Electrical conductor for motor windings, battery interconnects, PCB traces. Highest electrical conductivity of common metals (excluding silver). Used in motors, batteries, wiring. |

### MAT-004: Lithium (LFP cathode)

| Field | Value |
|---|---|
| id | MAT-004 |
| name | Lithium iron phosphate (LiFePO4 / LFP) |
| category | electrode |
| density_kg_m3 | 3600 |
| tensileStrength_MPa | N/A (ceramic) |
| thermalConductivity_W_mK | 1.5 |
| cost_USD_kg | 25 (cathode powder) |
| supplier | SPL-017 |
| notes | Cathode material for Li-ion batteries (LFP chemistry). Chosen for thermal stability (safer than NMC in field conditions), long cycle life (4000+ cycles), and lower cost. Lower energy density than NMC but adequate for agricultural robots. |

### MAT-005: Polymer (ABS / polycarbonate blend)

| Field | Value |
|---|---|
| id | MAT-005 |
| name | ABS/PC blend (polycarbonate-acrylonitrile butadiene styrene) |
| category | polymer |
| density_kg_m3 | 1100 |
| tensileStrength_MPa | 55 |
| thermalConductivity_W_mK | 0.2 |
| cost_USD_kg | 3.50 |
| supplier | SPL-018 |
| notes | Engineering plastic for non-structural housings, sensor enclosures, cable insulation. UV-stabilized grade for outdoor use. Impact-resistant. Moldable. Used for sensor housings, connector bodies, wire insulation. |

### MAT-006: Carbon fiber composite (T300 epoxy)

| Field | Value |
|---|---|
| id | MAT-006 |
| name | Carbon fiber composite (T300 epoxy) |
| category | composite |
| density_kg_m3 | 1600 |
| tensileStrength_MPa | 1500 |
| thermalConductivity_W_mK | 5 |
| cost_USD_kg | 35 |
| supplier | SPL-019 |
| notes | High-strength, low-weight composite for structural components where weight is critical (e.g., drone frames, lightweight robot arms). More expensive than aluminum. Used selectively where strength-to-weight ratio justifies cost. |

### MAT-007: Steel (1018 cold-rolled)

| Field | Value |
|---|---|
| id | MAT-007 |
| name | Steel (1018 cold-rolled) |
| category | metal |
| density_kg_m3 | 7870 |
| tensileStrength_MPa | 440 |
| thermalConductivity_W_mK | 51.9 |
| cost_USD_kg | 1.20 |
| supplier | SPL-020 |
| notes | Low-carbon steel for high-stress structural components (motor mounts, hitch points, load-bearing brackets). Heavier than aluminum but stronger and cheaper. Used where weight is less critical than cost. |

---

## Material summary

| ID | Material | Category | Cost ($/kg) | Primary use |
|---|---|---|---|---|
| MAT-001 | Aluminum 6061-T6 | metal | 4.50 | Structural (chassis, housings) |
| MAT-002 | Silicon | semiconductor | 50.00 | Electronics (processors, sensors, solar) |
| MAT-003 | Copper C11000 | metal | 9.00 | Electrical (windings, interconnects) |
| MAT-004 | LFP (cathode) | electrode | 25.00 | Battery (Li-ion) |
| MAT-005 | ABS/PC blend | polymer | 3.50 | Non-structural (housings, insulation) |
| MAT-006 | Carbon fiber T300 | composite | 35.00 | Lightweight structural (selective) |
| MAT-007 | Steel 1018 | metal | 1.20 | High-stress structural (mounts, brackets) |

---

## What this library does NOT do

- It does not cover all materials. The library is seeded with 7 materials sufficient for the example blueprint.
- It does not include material sourcing ethics (e.g., conflict minerals). That is a future consideration.
- It does not model material price volatility. Prices are point-in-time estimates.
- It does not modify the frozen formula or any prior architecture.

---

## Pre-stated falsifier (EP-4)

**Claim:** The 7 materials in this library are sufficient to manufacture the components in COMPONENT_LIBRARY.md.

**Falsifier:** A component in COMPONENT_LIBRARY.md that requires a material not in this library — e.g., a rare-earth magnet (neodymium) for high-efficiency motors, or a specific polymer for chemical resistance.

**Status:** PENDING. The example blueprint will test this. If the blueprint requires a material not in the library, the library is incomplete.
