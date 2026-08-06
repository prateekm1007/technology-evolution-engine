# ADJACENCY_REGISTRY — Phase 11D

**Status:** evidence layer (adjacency measurements).
**Location:** repo root.
**Phase:** 11D.

## Schema

```typescript
interface AdjacencyMeasurement {
    combination: string[];
    year: number;
    graphDistance: number;      // shortest path in REQUIRES graph
    dependencyDistance: number;  // depth of REQUIRES chain
    costDistance: number;        | cost_threshold - actual_cost |
    manufacturingDistance: number;  // TRL gap to manufacturing maturity
    regulatoryDistance: number;  // years to regulation in force
}
```

## Distance measurements for key combinations

### T=1995 (cost=$3000/kWh, UN38.3 not yet in force)

| Combination | Graph Dist | Dep Depth | Cost Dist | Mfg Dist | Reg Dist |
|---|---|---|---|---|---|
| {EES, INTERCALATION, CELL_ASSEMBLY} | 1 | 2 | 2900 | 0 | 8 |
| {EES, INTERCALATION, SoC} | 1 | 2 | 2900 | 0 | 8 |
| {EES, INTERCALATION, COATING} | 1 | 2 | 2900 | 0 | 8 |
| {EES, THERMAL_MGMT, SoC} | 2 | 3 | 2900 | 4 | 8 |

### T=2005 (cost=$500/kWh, UN38.3 in force since 2003)

| Combination | Graph Dist | Dep Depth | Cost Dist | Mfg Dist | Reg Dist |
|---|---|---|---|---|---|
| {EES, THERMAL_MGMT, SoC} | 2 | 3 | 400 | 0 | 0 |
| {EES, INTERCALATION, ELECTRON_COLL} | 1 | 2 | 400 | 0 | 0 |
| {EES, FAST_CHG, THERMAL_MGMT, SAFETY} | 3 | 4 | 400 | 2 | 0 |

### T=2010 (cost=$300/kWh)

| Combination | Graph Dist | Dep Depth | Cost Dist | Mfg Dist | Reg Dist |
|---|---|---|---|---|---|
| {EES, FAST_CHG, THERMAL_MGMT, SAFETY} | 3 | 4 | 200 | 0 | 0 |
| {FAST_CHG, THERMAL_MGMT} | 1 | 2 | 200 | 0 | 0 |

### T=2015 (cost=$200/kWh)

| Combination | Graph Dist | Dep Depth | Cost Dist | Mfg Dist | Reg Dist |
|---|---|---|---|---|---|
| {EES, COATING, CELL_ASSEMBLY} | 2 | 3 | 100 | 0 | 0 |
| {FAST_CHG, THERMAL_MGMT, SAFETY} | 2 | 3 | 100 | 0 | 0 |

## Key observations

1. **Cost distance shrinks over time.** In 1995, cost distance was
   $2900 (cost $3000 vs threshold $100). By 2015, it was $100 ($200
   vs $100). This shrinking distance correlates with invention events.

2. **Regulatory distance shrinks to zero.** Before 2003, UN38.3 was
   8 years away. After 2003, it's 0. The regulatory gate opening
   correlates with deployment.

3. **Graph distance is small for actual outcomes (1-3).** All actual
   outcomes are within 3 hops of the root capability graph. This
   confirms the adjacency hypothesis: inventions emerge CLOSE to
   existing combinations, not far away.

4. **Manufacturing distance is 0 for most actual outcomes.** This
   means manufacturing capabilities (ELECTRODE_COATING, CELL_ASSEMBLY)
   were mature when the invention happened — manufacturing was not
   the bottleneck.
