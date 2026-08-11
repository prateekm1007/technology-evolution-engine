# VERTICAL_SCOPE — Phase 7A Corpus Definition

**Status:** frozen corpus definition (constitutional).
**Location:** repo root.
**Phase:** 7A (per CEO authorization CEO-7A-7D).
**Commit baseline:** `f7f2e14`.

> Build the smallest machine capable of proving that the larger
> machine is possible.
> — CEO authorization, Phase 7

This document freezes the single experimental domain for the
CAPABILITY_MODEL. It defines what is IN scope and what is OUT.
Any addition requires explicit CEO authorization per
ONTOLOGY_FREEZE.md.

---

## 1. The vertical (frozen)

```text
electrochemical energy storage
```

This vertical covers: batteries (lithium-ion, solid-state,
flow), supercapacitors, fuel cells (as they relate to storage),
and the capabilities/constraints/infrastructure that enable them.

### What is IN scope

- Electrochemical cells (anode, cathode, electrolyte, separator)
- Battery management systems
- Charging/discharging infrastructure
- Manufacturing processes for battery components
- Materials used in electrochemical storage
- Regulations governing battery safety, shipping, and recycling
- Markets for electrochemical storage (EV, grid, consumer)
- Products that are electrochemical storage devices

### What is OUT of scope (explicitly)

- Non-electrochemical storage (pumped hydro, compressed air,
  thermal storage, flywheels)
- Energy generation (solar, wind, nuclear) — these are
  UPSTREAM capabilities, not storage
- Energy distribution (grid management) — this is INFRASTRUCTURE
  that enables storage, not storage itself
- Semiconductor manufacturing (unless directly for battery
  management circuits)
- Consumer electronics (unless the product IS a battery)

### Why this vertical

Per CEO directive: "electrochemical energy storage." This is the
vertical the CEO chose. It has:
- Rich patent history (USPTO CPC H01M)
- Active scientific literature (arXiv, Nature, Science)
- Real products (Tesla 4680, Panasonic NCR, etc.)
- Known constraints (energy density limits, safety regulations,
  cost thresholds)
- Historical data for frozen-time backtesting (lithium-ion
  evolved from 1991 to 2026)

---

## 2. Maximum scope (frozen per ONTOLOGY_FREEZE.md)

| Entity       | Maximum | Source |
|---|---:|---|
| Patents      | 50 | CEO authorization + ONTOLOGY_FREEZE.md |
| Papers       | 50 | CEO authorization + ONTOLOGY_FREEZE.md |
| Products     | 10 | CEO authorization + ONTOLOGY_FREEZE.md |
| Capabilities | 20 | CEO authorization + ONTOLOGY_FREEZE.md |
| Constraints  | 10 | CEO authorization + ONTOLOGY_FREEZE.md |
| Edge types   | 6 (of 9 defined) | CAPABILITY_ONTOLOGY.md Section 6 |
| Node types   | 10 (all defined) | CAPABILITY_ONTOLOGY.md Section 4 |
| Verticals    | 1 | ONTOLOGY_FREEZE.md |

### Edge type selection (6 of 9)

The CAPABILITY_MODEL defines 9 edge types. For this vertical,
the 6 most relevant are:

1. **REQUIRES** — a capability needs another to function
   (e.g., ENERGY_STORAGE REQUIRES ION_TRANSPORT)
2. **ENABLES** — a capability makes another possible
   (e.g., FAST_CHARGING ENABLES EV_ADOPTION)
3. **SUBSTITUTES_FOR** — one capability can replace another
   (e.g., SUPERCAPACITOR_STORAGE SUBSTITUTES_FOR BATTERY_STORAGE
   in high-power, low-energy applications)
4. **CONSTRAINS** — a constraint limits a capability's performance
   (e.g., ENERGY_DENSITY_LIMIT CONSTRAINS BATTERY_CAPACITY)
5. **EMBODIED_IN** — a capability is physically realized by a
   material/process (e.g., ION_TRANSPORT EMBODIED_IN LITHIUM_ELECTROLYTE)
6. **REGULATED_BY** — a capability is subject to a regulation
   (e.g., BATTERY_SHIPPING REGULATED_BY UN38_3)

The 3 edge types NOT used in this vertical:
- BLOCKS (no clear use case in electrochemical storage)
- DEPENDS_ON (subsumed by REQUIRES for this vertical)
- REDUCES_COST_OF (no clear use case yet; may be added if
  cost-curve analysis warrants it, but requires ONTOLOGY_FREEZE
  justification)

---

## 3. Temporal scope

### Historical period for backtesting

```text
1990 — 2026
```

- 1990: pre-lithium-ion commercialization (Sony, 1991). The
  "adjacent possible" at this point does not include lithium-ion
  at scale.
- 2026: current state. The system's knowledge as of now.

### Frozen-time backtest points

Per CEO Phase 7D:

```text
T = 1995, 2000, 2005, 2010, 2015, 2020
```

At each T, the system's knowledge is restricted to data available
at T. Predictions are ranked possibilities. Validation is outcomes
at T+5 to T+10.

---

## 4. Data sources

### Patents (50 max)

- Source: USPTO (via Google Patents)
- CPC code: H01M (PROCESSES OR MEANS FOR THE DIRECT CONVERSION OF
  CHEMICAL ENERGY INTO ELECTRICAL ENERGY)
- Date range: 1990-2026
- Selection: most-cited patents in H01M, sampled across the
  date range

### Papers (50 max)

- Sources: arXiv, Nature, Science, Journal of the Electrochemical
  Society
- Date range: 1990-2026
- Selection: highly-cited papers + recent reviews

### Products (10 max)

- Sources: public product specifications, industry reports
- Examples: Tesla 4680, Panasonic NCR18650B, A123 LFP,
  Samsung SDI, LG Chem, CATL blade, Toyota solid-state prototype
- Selection: products that represent distinct capability
  combinations

---

## 5. What this document does NOT do

- It does NOT authorize ingestion (that's Phase 7B/7C work, which
  follows this definition).
- It does NOT define the capabilities or constraints (those are in
  CAPABILITY_CATALOG.md and CONSTRAINT_CATALOG.md).
- It does NOT modify the Phase 5 CO_OCCURRENCE_MODEL baseline.
- It does NOT exceed the ONTOLOGY_FREEZE.md caps.

---

## 6. Enforcement

This scope is frozen. Any addition (more patents, more papers,
more products, a 2nd vertical, an 11th node type, a 10th edge
type) requires explicit CEO authorization per ONTOLOGY_FREEZE.md.
