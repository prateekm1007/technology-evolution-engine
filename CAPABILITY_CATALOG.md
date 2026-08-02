# CAPABILITY_CATALOG — Phase 7A

**Status:** frozen capability catalog (20 capabilities, at ONTOLOGY_FREEZE cap).
**Phase:** 7A.

The 20 capabilities for the electrochemical energy storage vertical.
Each capability is a node of type CAPABILITY in the CAPABILITY_MODEL.
These are the primitives — the things technologies CAN DO, not the
things they ARE.

---

## 1. Storage capabilities

| # | Capability | Description | Example embodiments |
|---|---|---|---|
| 1 | ELECTROCHEMICAL_ENERGY_STORAGE | Store energy via electrochemical reactions | Li-ion cell, solid-state cell, flow cell |
| 2 | HIGH_POWER_DISCHARGE | Release energy rapidly (high C-rate) | Supercapacitor, LFP cell, power battery |
| 3 | HIGH_ENERGY_DENSITY_STORAGE | Store large energy per unit mass/volume | NCM cell, solid-state cell |
| 4 | LONG_CYCLE_LIFE_STORAGE | Maintain capacity over many charge/discharge cycles | LFP cell, LTO cell |
| 5 | FAST_CHARGING | Accept charge at high rate without degradation | 800V architecture, LFP fast-charge |

## 2. Ion transport capabilities

| # | Capability | Description | Example embodiments |
|---|---|---|---|
| 6 | ION_TRANSPORT | Move ions between electrodes through electrolyte | Liquid electrolyte, solid electrolyte, gel |
| 7 | SELECTIVE_ION_TRANSPORT | Transport specific ions while blocking others | Separator membrane, solid electrolyte |

## 3. Electrode capabilities

| # | Capability | Description | Example embodiments |
|---|---|---|---|
| 8 | INTERCALATION | Insert/remove ions into/from electrode material lattice | Graphite anode, LFP cathode, NCM cathode |
| 9 | CONVERSION_REACTION | Store energy via chemical conversion (not intercalation) | Li-S cathode, Li-air cathode |
| 10 | ELECTRON_COLLECTION | Collect/distribute electrons at electrode | Current collector (Al, Cu foil) |

## 4. Thermal capabilities

| # | Capability | Description | Example embodiments |
|---|---|---|---|
| 11 | THERMAL_MANAGEMENT | Maintain cell temperature within safe operating range | Cooling plate, thermal interface material |
| 12 | RADIATIVE_COOLING | Passive cooling via radiative emission | (cross-domain capability from Phase 5) |

## 5. Management capabilities

| # | Capability | Description | Example embodiments |
|---|---|---|---|
| 13 | STATE_OF_CHARGE_MONITORING | Measure remaining charge in a cell | BMS, coulomb counting, voltage lookup |
| 14 | CELL_BALANCING | Equalize charge across cells in a pack | Active balancing, passive balancing |
| 15 | SAFETY_PROTECTION | Prevent thermal runaway, overcharge, short circuit | CID, PTC, fuse, BMS cutoff |

## 6. Manufacturing capabilities

| # | Capability | Description | Example embodiments |
|---|---|---|---|
| 16 | ELECTRODE_COATING | Coat active material onto current collector | Slot-die coating, dry electrode |
| 17 | CELL_ASSEMBLY | Assemble electrodes, separator, electrolyte into a cell | Winding, stacking, pouch, prismatic |
| 18 | SOLID_ELECTROLYTE_SINTERING | Densify solid electrolyte at elevated temperature | Hot pressing, spark plasma sintering |

## 7. Infrastructure capabilities

| # | Capability | Description | Example embodiments |
|---|---|---|---|
| 19 | GRID_INTERCONNECTION | Connect storage system to the electrical grid | Inverter, transformer, grid-tie |
| 20 | RECYCLING | Recover materials from end-of-life cells | Hydrometallurgical, pyrometallurgical |

---

## Notes

- These 20 capabilities are at the ONTOLOGY_FREEZE.md cap. No 21st
  capability may be added without explicit CEO authorization.
- Each capability is a PRIMITIVE — it describes WHAT can be done,
  not HOW. The "how" is embodied in MATERIAL, PROCESS, and PRODUCT
  nodes connected via EMBODIED_IN edges.
- Some capabilities span multiple sub-domains (e.g., RADIATIVE_COOLING
  is cross-domain, carried over from the CO_OCCURRENCE_MODEL's Phase 5
  work). This is intentional — capabilities are reusable across
  applications.
- The selection prioritizes the core value chain: storage → transport
  → electrodes → thermal → management → manufacturing → infrastructure.
  This covers the full lifecycle from material to end-of-life.
