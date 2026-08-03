# CONSTRAINT_CATALOG — Phase 7A

**Status:** frozen constraint catalog (10 constraints, at ONTOLOGY_FREEZE cap).
**Phase:** 7A.

The 10 constraints for the electrochemical energy storage vertical.
Each constraint is a node of type CONSTRAINT in the CAPABILITY_MODEL.
Constraints LIMIT capabilities — they define the feasibility gates
(Feasibility Score C).

---

## Physical constraints

| # | Constraint | Type | Limit | Affected capabilities |
|---|---|---|---|---|
| 1 | THEORETICAL_ENERGY_DENSITY_LIMIT | Physical | ~400 Wh/kg (Li-ion chemistry ceiling) | HIGH_ENERGY_DENSITY_STORAGE |
| 2 | ION_TRANSPORT_RESISTANCE | Physical | Electrolyte ionic conductivity limits C-rate | ION_TRANSPORT, HIGH_POWER_DISCHARGE |
| 3 | THERMAL_RUNAWAY_THRESHOLD | Physical | Cell temperature > ~150°C triggers runaway | All storage capabilities, SAFETY_PROTECTION |

## Manufacturing constraints

| # | Constraint | Type | Limit | Affected capabilities |
|---|---|---|---|---|
| 4 | SOLID_ELECTROLYTE_DENSIFICATION | Manufacturing | Cannot achieve >95% density without sintering | SOLID_ELECTROLYTE_SINTERING, ION_TRANSPORT |
| 5 | DRY_ELECTRODE_YIELD | Manufacturing | Dry electrode process yield < 90% at scale | ELECTRODE_COATING |

## Economic constraints

| # | Constraint | Type | Limit | Affected capabilities |
|---|---|---|---|---|
| 6 | COST_PER_KWH_THRESHOLD | Economic | EV: <$100/kWh; Grid: <$0.05/kWh-cycle | All storage capabilities |
| 7 | MATERIAL_SCARCITY | Economic | Lithium, cobalt, nickel supply-limited | INTERCALATION, HIGH_ENERGY_DENSITY_STORAGE |

## Regulatory constraints

| # | Constraint | Type | Limit | Affected capabilities |
|---|---|---|---|---|
| 8 | UN38_3_SHIPPING_SAFETY | Regulatory | Must pass UN38.3 testing for transport | All storage, BATTERY_SHIPPING |
| 9 | IEC_62133_SAFETY_STANDARD | Regulatory | Must meet IEC 62133 for consumer products | SAFETY_PROTECTION, CELL_ASSEMBLY |

## Infrastructure constraints

| # | Constraint | Type | Limit | Affected capabilities |
|---|---|---|---|---|
| 10 | GRID_CAPACITY_LIMIT | Infrastructure | Grid interconnection capacity may be insufficient | GRID_INTERCONNECTION |

---

## Notes

- These 10 constraints are at the ONTOLOGY_FREEZE.md cap. No 11th
  constraint may be added without explicit CEO authorization.
- Each constraint maps to one or more Feasibility gates (F1-F5 in
  FEASIBILITY.md):
  - Physical → F5 (physical gate)
  - Manufacturing → F3 (manufacturing gate)
  - Economic → F2 (economic gate)
  - Regulatory → F1 (regulatory gate)
  - Infrastructure → F4 (infrastructure gate)
- The constraints are typed — this matters because the Feasibility
  score is boolean AND across gates, but the constraint TYPE determines
  which gate it belongs to.
- Some constraints are temporal (e.g., COST_PER_KWH_THRESHOLD changes
  over time). These require TemporalState (validFrom/validTo) per
  CAPABILITY_ONTOLOGY.md Section 10.
