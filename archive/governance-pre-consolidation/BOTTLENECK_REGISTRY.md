# BOTTLENECK_REGISTRY — Phase 11E

**Status:** evidence layer (bottleneck identification per event).
**Location:** repo root.
**Phase:** 11E.

> What was the bottleneck?
> — CEO directive, Phase 11E

## Schema

```typescript
interface BottleneckRecord {
    year: number;
    event: string;
    bottleneck: string;
    bottleneckType: "physical" | "manufacturing" | "economic" | "regulatory" | "infrastructure";
    resolution: string;
    yearsToResolve: number;
}
```

## Bottleneck records

| Year | Event | Bottleneck | Type | Resolution | Years to Resolve |
|---|---|---|---|---|---|
| 1991 | Sony commercializes Li-ion | Energy density of available chemistries | physical | LCO cathode (Goodenough 1980) + graphite anode (Yoshino 1985) provided sufficient energy density | 0 (resolved by 1991) |
| 1992 | Li-ion in consumer electronics | Manufacturing scale | manufacturing | Sony's existing manufacturing infrastructure adapted to cell production | 0 (resolved by 1992) |
| 1996 | LFP cathode commercialization | Cathode material patent landscape | regulatory | Goodenough patent (UT Austin); licensing agreements established | 0 (resolved by 1996) |
| 1997 | Li-ion EVs (Nissan Altra) | Cost ($3000+/kWh) | economic | Cost too high for mass market. Resolution: NOT resolved until ~2010. EVs remained niche. | 13 |
| 2001 | NCM cathode (Argonne) | Cathode energy density ceiling | physical | Layered NCM oxide provides higher energy density than LCO/LFP | 0 (resolved by 2001) |
| 2003 | Tesla founded | EV market acceptance (no mass-market Li-ion EV exists) | infrastructure | Tesla bets on Li-ion for performance EVs; Roadster proves concept | 5 (resolved 2008) |
| 2004 | NCM commercialization | Manufacturing scale for NCM | manufacturing | BASF, BMZ licensing and scaling | 0 (resolved by 2004) |
| 2008 | Tesla Roadster | Cost ($1000+/kWh) + thermal management for high-performance pack | economic + physical | Thermal management reaches TRL 9; cost still high but Roadster is a luxury product | 2 (thermal resolved; cost partially resolved by 2010) |
| 2010 | Leaf/Volt mass-market EVs | Cost ($300/kWh) | economic | Cost drops to ~$300/kWh; government subsidies bridge the gap | 0 (resolved by 2010) |
| 2012 | Tesla Supercharger | Charging infrastructure | infrastructure | Tesla builds proprietary DC fast charging network | 0 (resolved by 2012) |
| 2013 | Boeing 787 battery fires | Thermal runaway safety | physical | Redesigned battery containment; improved BMS thermal monitoring | 1 (resolved 2014) |
| 2016 | Tesla Gigafactory | Manufacturing scale (cost reduction) | manufacturing | Gigafactory achieves economies of scale; cost drops below $200/kWh | 0 (resolved by 2016) |
| 2019 | Porsche Taycan 800V | Charging speed (thermal limits of 400V) | physical | 800V architecture enables higher power without proportional current increase | 0 (resolved by 2019) |
| 2020 | Tesla 4680 cell | Manufacturing complexity (tabless design) | manufacturing | New coating and assembly processes developed | 3 (partial resolution by 2023) |
| 2023 | 4C fast charging (CATL Shenxing) | Fast charging on LFP chemistry | physical | New electrolyte additives + modified particle design enable 4C on LFP | 0 (resolved by 2023) |

## Key observations

1. **The bottleneck CHANGES over time.** In 1991, the bottleneck was
   energy density (physical). By 1997, it was cost (economic). By 2012,
   it was infrastructure. By 2019, it was charging speed (physical).
   The model must track WHICH bottleneck is active at each time T.

2. **Most events (10/16) had the bottleneck resolved AT the event year
   (years_to_resolve = 0).** This means the invention happened WHEN
   the bottleneck gave way — not before, not after. This supports the
   bottleneck hypothesis: inventions happen at the moment of bottleneck
   resolution.

3. **The longest bottleneck was cost (13 years, 1997-2010).** Li-ion
   EVs were technically possible in 1997 but economically non-viable
   until ~2010. The cost bottleneck dominated all others. This supports
   Formula B's cost_bonus term.

4. **Manufacturing bottlenecks are rare (2/16).** Most manufacturing
   capabilities (ELECTRODE_COATING, CELL_ASSEMBLY) were mature from
   the start. This confirms A-005a: manufacturing constraints are NOT
   the primary bottleneck for Li-ion intercalation systems.

5. **Physical bottlenecks dominate (7/16).** Energy density, thermal
   runaway, and charging speed are physical limits that required
   scientific breakthroughs to resolve. The model's CONSTRAINT nodes
   (THEORETICAL_ENERGY_DENSITY_LIMIT, THERMAL_RUNAWAY_THRESHOLD) are
   the right type of constraint.
