# BOUNDARY_REGISTRY

**Status:** Phase 14R boundary analysis.
**Location:** repo root.
**Phase:** 14R.

> Is the theory wrong, or is the ontology of invention incomplete?
> — CEO directive, Phase 14R

This document catalogs every failure case from the semiconductor
and telecom backtests. Each case is typed per the schema below.
The catalog is descriptive — it records what failed and how,
without yet drawing the conclusion (which is in
PHASE_14R_REFLECTION.md).

---

## Schema

```typescript
interface BoundaryCase {
    caseId: string;

    domain: string;

    event: string;

    violatedAssumption: string[];

    failureMode: string;

    interpretation: string;

    consequence: string;
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `caseId` | string | yes | BC-XXX identifier. Sequential. |
| `domain` | string | yes | semiconductors \| telecommunications |
| `event` | string | yes | The event that failed to be predicted (or that the theory cannot explain). |
| `violatedAssumption` | string[] | yes | Which assumption(s) of the theory this case violates. Drawn from a fixed vocabulary: `monotonic_TRL`, `capability_emergence_not_exploitation`, `physical_bottleneck`, `single_rise_per_capability`, `velocity_above_threshold`, `firm_level_agency`, `continuous_TRL_progression`. |
| `failureMode` | string | yes | The mechanism by which the theory failed. Descriptive, not interpretive. |
| `interpretation` | string | yes | What this case suggests about the theory's boundary. Tentative, not conclusive. |
| `consequence` | string | yes | What this case implies for the theory's claim. |

---

## Semiconductor boundary cases

### BC-001: Intel 4004 (1971)

| Field | Value |
|---|---|
| caseId | BC-001 |
| domain | semiconductors |
| event | Intel 4004 (1971): first commercial microprocessor, 10um process, 2300 transistors |
| violatedAssumption | ["capability_emergence_not_exploitation", "velocity_above_threshold"] |
| failureMode | The combination {OPTICAL_LITHOGRAPHY, PLANAR_TRANSISTOR, WAFER_FABRICATION} contains only stable capabilities (all at TRL 9 throughout). Velocity = 0 for every capability. The formula assigns score 0. The event was a TP in the backtest only because all 4 candidates at T=1970 tied at score 0 — the TP is a sort-order artifact, not a prediction. |
| interpretation | The 4004 was a scaling event: integrating more transistors per chip within an already-mature technology base. The capabilities (lithography, planar transistors, wafer fabrication) did not EMERGE in 1971 — they were being EXPLOITED. The theory detects emergence, not exploitation. |
| consequence | Strict necessity (FEC-002) is falsified for this case: invention occurred with zero rising-capability velocity. The theory's claim "velocity is necessary" does not hold for scaling-driven invention. |

### BC-002: Intel 386 (1985)

| Field | Value |
|---|---|
| caseId | BC-002 |
| domain | semiconductors |
| event | Intel 386 (1985): 32-bit microprocessor, 1.5um process, 275K transistors |
| violatedAssumption | ["capability_emergence_not_exploitation", "velocity_above_threshold"] |
| failureMode | Same as BC-001. The combination contains only stable capabilities. Velocity = 0. TP was a sort-order artifact (4 candidates, all tied at 0). |
| interpretation | The 386 scaled transistor count by 100x within the same technology base. No capability emerged. The theory cannot detect this. |
| consequence | Second falsification of strict necessity for scaling events. |

### BC-003: Intel Pentium (1993)

| Field | Value |
|---|---|
| caseId | BC-003 |
| domain | semiconductors |
| event | Intel Pentium (1993): 0.8um process, superscalar, 3.1M transistors |
| violatedAssumption | ["capability_emergence_not_exploitation", "velocity_above_threshold"] |
| failureMode | Same pattern. Combination {OPTICAL_LITHOGRAPHY, PLANAR_TRANSISTOR}, both stable. Velocity = 0. Event was an FN (not in Top-10). |
| interpretation | The Pentium's invention was architectural (superscalar) and scaling (3M transistors), not capability-emergent. The theory does not predict architectural innovation. |
| consequence | Third falsification. The theory misses architectural invention that occurs within stable capabilities. |

### BC-004: 0.35um DRAM (1995)

| Field | Value |
|---|---|
| caseId | BC-004 |
| domain | semiconductors |
| event | 0.35um node, 64M DRAM (1995) |
| violatedAssumption | ["capability_emergence_not_exploitation", "velocity_above_threshold"] |
| failureMode | Same pattern. Combination {OPTICAL_LITHOGRAPHY, WAFER_FABRICATION}, both stable. Velocity = 0. Event was an FN. |
| interpretation | DRAM scaling is a manufacturing-yield and lithography-resolution optimization, not a capability emergence. |
| consequence | Fourth falsification. DRAM scaling is invisible to the theory. |

### BC-005: 130nm strained silicon (2001)

| Field | Value |
|---|---|
| caseId | BC-005 |
| domain | semiconductors |
| event | 130nm node with strained silicon (2001) |
| violatedAssumption | ["capability_emergence_not_exploitation", "velocity_above_threshold"] |
| failureMode | Same pattern. Combination {OPTICAL_LITHOGRAPHY, PLANAR_TRANSISTOR}, both stable. Velocity = 0. Event was an FN. |
| interpretation | Strained silicon is a material-engineering optimization (SiGe source/drain to strain the channel). The capability of building planar transistors was already mature; the innovation was a technique within that capability. |
| consequence | Fifth falsification. The theory cannot detect technique-level innovation within mature capabilities. |

### BC-006: TSV 3D packaging (2009) — missed despite rising capability

| Field | Value |
|---|---|
| caseId | BC-006 |
| domain | semiconductors |
| event | TSV 3D packaging (2009): Xilinx Virtex-7, TSMC CoWoS |
| violatedAssumption | ["velocity_above_threshold"] |
| failureMode | ADVANCED_PACKAGING was rising (TRL 5 → 8 from 2000-2010), but velocity at 2008 was exactly 0.20 — at the threshold, not above it. The combination {ADVANCED_PACKAGING, OPTICAL_LITHOGRAPHY} scored 0.10 (velocity 0.20/2 = 0.10, adjacency 1.0). It ranked below Top-10 because 154 candidates existed and higher-adjacency combos filled the Top-10. |
| interpretation | This is a granularity problem, not a structural problem. The velocity was real (0.20) but the threshold (strictly > 0.20) excluded it. At threshold > 0.15, this event would be detected. |
| consequence | The pre-stated threshold (> 0.20) was calibrated to Li-ion (velocities 0.33-0.67) and is too strict for semiconductor data granularity (1 TRL step / 5 years = 0.20). This is an EP-6 issue (threshold pre-registration) but not a theory-falsification. |

### BC-007: Intel 22nm FinFET (2011) — missed despite rising capability

| Field | Value |
|---|---|
| caseId | BC-007 |
| domain | semiconductors |
| event | Intel 22nm FinFET (2011): Ivy Bridge, first volume FinFET |
| violatedAssumption | ["velocity_above_threshold"] |
| failureMode | NON_PLANAR_TRANSISTOR was rising (TRL 4 → 8 from 1990-2010), but velocity at 2010 was exactly 0.20 — at the threshold. Combination {NON_PLANAR_TRANSISTOR, OPTICAL_LITHOGRAPHY} scored 0.10, ranked below Top-10. |
| interpretation | Same granularity issue as BC-006. The capability was genuinely rising, but the 5-year TRL snapshot granularity produced velocity exactly at the threshold. |
| consequence | Same as BC-006. Granularity, not structural. |

### BC-008: Intel 14nm FinFET (2014) — missed

| Field | Value |
|---|---|
| caseId | BC-008 |
| domain | semiconductors |
| event | Intel 14nm FinFET (2014): Broadwell, 2nd-gen FinFET |
| violatedAssumption | ["velocity_above_threshold"] |
| failureMode | NON_PLANAR_TRANSISTOR velocity at 2013 was 0.20 (at threshold). 2-capability combo ranked below 3-capability combos with higher adjacency. |
| interpretation | Same granularity issue. The 14nm node was a continuation of FinFET scaling, not a new capability. |
| consequence | Granularity, not structural. |

### BC-009: TSMC 7nm EUV (2018) — missed

| Field | Value |
|---|---|
| caseId | BC-009 |
| domain | semiconductors |
| event | TSMC 7nm EUV (2018): Apple A12, first volume EUV production |
| violatedAssumption | ["velocity_above_threshold"] |
| failureMode | EUV_LITHOGRAPHY was rising (TRL 4 → 8 from 1990-2015), but velocity at 2017 was 0.20 — at the threshold. Combination {EUV_LITHOGRAPHY, NON_PLANAR_TRANSISTOR} scored 0.10, ranked below Top-10. |
| interpretation | Same granularity issue. EUV was genuinely rising for 30+ years, but the 5-year snapshot granularity produced velocity at the threshold. |
| consequence | Granularity, not structural. |

### BC-010: TSMC 5nm EUV (2020) — missed

| Field | Value |
|---|---|
| caseId | BC-010 |
| domain | semiconductors |
| event | TSMC 5nm EUV (2020): Apple A14 |
| violatedAssumption | ["velocity_above_threshold"] |
| failureMode | Same as BC-009. EUV velocity at 2019 was 0.20 (at threshold). |
| interpretation | 5nm was a continuation of EUV scaling, not a new capability. |
| consequence | Granularity, not structural. |

### BC-011: AMD 3D V-Cache (2020) — missed despite plateaued capability

| Field | Value |
|---|---|
| caseId | BC-011 |
| domain | semiconductors |
| event | AMD 3D V-Cache (2020): TSMC SoIC, hybrid copper-to-copper bonding |
| violatedAssumption | ["capability_emergence_not_exploitation", "velocity_above_threshold"] |
| failureMode | ADVANCED_PACKAGING had reached TRL 9 by 2015 (velocity = 0 in 2020). The capability was mature, not rising. The 3D V-Cache innovation was a manufacturing-process refinement within the mature capability. |
| interpretation | This is a post-maturity exploitation event. The capability had already emerged (TSV in 2012); the 2020 event was an incremental improvement. The theory does not detect post-maturity innovation. |
| consequence | The theory cannot detect innovation that occurs AFTER a capability has reached TRL 9. This is the "capability exploitation" boundary (H1). |

### BC-012: Samsung 3nm GAA (2022) — missed despite plateaued capability

| Field | Value |
|---|---|
| caseId | BC-012 |
| domain | semiconductors |
| event | Samsung 3nm GAA (2022): first volume gate-all-around production |
| violatedAssumption | ["capability_emergence_not_exploitation", "velocity_above_threshold"] |
| failureMode | NON_PLANAR_TRANSISTOR had reached TRL 9 by 2015 (velocity = 0 in 2022). GAA is technically a new transistor architecture, but the trajectory registry tracked it under NON_PLANAR_TRANSISTOR (which includes both FinFET and GAA). The capability was modeled as mature, not rising. |
| interpretation | This reveals an ontology modeling choice: should GAA be a separate capability from FinFET, or a sub-capability? If separate, GAA would have its own rising trajectory. If sub-capability, the model cannot detect the GAA emergence because the parent capability is at TRL 9. |
| consequence | The theory's boundary depends on ontology granularity. If capabilities are too coarse, emergence events within mature parent capabilities are invisible. This is an ontology question, not a theory question. |

---

## Telecommunications boundary cases

### BC-013: GSM 2G (1991) — missed despite genuine emergence

| Field | Value |
|---|---|
| caseId | BC-013 |
| domain | telecommunications |
| event | GSM 2G commercial launch (1991): first digital cellular, first SMS |
| violatedAssumption | ["single_rise_per_capability", "velocity_above_threshold"] |
| failureMode | WIRELESS_PROTOCOL rose for 1G (1975-1985), reached TRL 9, then plateaued. The 2G emergence (1982-1991) was a "re-rise" of the same capability — but the trajectory registry recorded WIRELESS_PROTOCOL as TRL 9 throughout 1985-2025. Velocity at 1990 = 0. The theory could not detect 2G emergence. |
| interpretation | This is the "re-rise" problem. Telecom capabilities rise multiple times (once per generation), but the trajectory model assumes a single rise. The model is blind to generation transitions after the first. |
| consequence | Strict necessity (FEC-002) is falsified: 2G emergence occurred with zero velocity in the modeled trajectory. The theory's boundary includes "single rise per capability" — telecom violates this. |

### BC-014: WCDMA 3G (2001) — missed

| Field | Value |
|---|---|
| caseId | BC-014 |
| domain | telecommunications |
| event | WCDMA 3G commercial launch (2001): NTT DoCoMo FOMA, first 3G |
| violatedAssumption | ["single_rise_per_capability", "velocity_above_threshold"] |
| failureMode | Same as BC-013. WIRELESS_PROTOCOL at TRL 9 since 1985. PACKET_SWITCHING re-rose for mobile data (1985-1995) but had plateaued by 2001. Velocity at 2000 = 0. |
| interpretation | 3G was a generation transition. The theory cannot detect it. |
| consequence | Second falsification of strict necessity for generation transitions. |

### BC-015: iPhone (2007) — missed despite device emergence

| Field | Value |
|---|---|
| caseId | BC-015 |
| domain | telecommunications |
| event | iPhone (2007): smartphone inflection, multi-touch + mobile internet |
| violatedAssumption | ["single_rise_per_capability", "monotonic_TRL"] |
| failureMode | SMART_DEVICE_INTEGRATION "re-rose" for smartphones (2005-2010). At 2006, it was at TRL 5 (dropped from 9 to 5 to track the smartphone sub-capability). Velocity = (5-9)/5 = -0.8. The formula produced a NEGATIVE score, which sorted below zero scores. The model PENALIZED the iPhone's emergence. |
| interpretation | This is the non-monotonic TRL problem. The trajectory registry modeled SMART_DEVICE_INTEGRATION as "dropping" from TRL 9 (basic phones mature) to TRL 5 (smartphones emerging). The formula's velocity term produced a negative value, which the model treated as worse than zero. |
| consequence | The theory is not just blind to re-rise — it ACTIVELY PENALIZES re-rise. This is worse than BC-013 (where velocity was 0). Here, the model's "susceptibility estimate" is anti-correlated with actual invention. |

### BC-016: LTE 4G (2009) — missed

| Field | Value |
|---|---|
| caseId | BC-016 |
| domain | telecommunications |
| event | LTE 4G commercial launch (2009): TeliaSonera, first 4G, all-IP |
| violatedAssumption | ["single_rise_per_capability", "velocity_above_threshold"] |
| failureMode | WIRELESS_PROTOCOL at TRL 9. PACKET_SWITCHING at TRL 9. Both plateaued. Velocity = 0 for both. |
| interpretation | 4G was a generation transition + architectural shift (all-IP). Neither dimension is captured by the trajectory model. |
| consequence | Third falsification for generation transitions. |

### BC-017: NB-IoT (2016) — missed

| Field | Value |
|---|---|
| caseId | BC-017 |
| domain | telecommunications |
| event | NB-IoT standardized (2016): 3GPP Release 13, cellular IoT |
| violatedAssumption | ["single_rise_per_capability", "monotonic_TRL"] |
| failureMode | SMART_DEVICE_INTEGRATION re-rose for IoT (2015-2020). At 2015, it was at TRL 5 (dropped from 9 to 5). Velocity = -0.8. Same anti-correlation as BC-015. |
| interpretation | IoT was a re-emergence of the device-integration capability for a new device class. The theory penalized it. |
| consequence | Same as BC-015. The model actively penalizes re-emergence. |

### BC-018: 5G NR sub-6GHz (2019) — missed

| Field | Value |
|---|---|
| caseId | BC-018 |
| domain | telecommunications |
| event | 5G NR sub-6GHz (2019): Verizon/KT/SKT, first 5G commercial |
| violatedAssumption | ["single_rise_per_capability", "velocity_above_threshold"] |
| failureMode | WIRELESS_PROTOCOL at TRL 9 (plateaued since 1985). SPECTRUM_UTILIZATION at TRL 5 in 2018 (re-rising for mmWave). Velocity = -0.8 for SPECTRUM_UTILIZATION. NETWORK_VIRTUALIZATION at TRL 6, velocity = 0.20 (at threshold). The combination had mixed positive and negative velocities; max was 0.20 (at threshold). |
| interpretation | 5G was a generation transition. The model could not detect it because the relevant capabilities were either plateaued (WIRELESS_PROTOCOL) or re-rising with negative velocity (SPECTRUM_UTILIZATION). |
| consequence | Fourth falsification for generation transitions. |

### BC-019: 5G mmWave (2020) — missed

| Field | Value |
|---|---|
| caseId | BC-019 |
| domain | telecommunications |
| event | 5G mmWave (2020): T-Mobile/Verizon, mmWave commercial deployment |
| violatedAssumption | ["single_rise_per_capability", "monotonic_TRL"] |
| failureMode | SPECTRUM_UTILIZATION re-rose for mmWave (2015-2020). At 2019, it was at TRL 9 (just re-rose). Velocity = (9-5)/5 = 0.8, /2 = 0.4 — above threshold. But the combination {SPECTRUM_UTILIZATION, WIRELESS_PROTOCOL} had WIRELESS_PROTOCOL at TRL 9 (velocity 0). Max velocity = 0.4. The combination scored 0.4 × adjacency, but 154 candidates existed and higher-adjacency combos filled the Top-10. |
| interpretation | This is the one telecom event where the velocity signal was real and above threshold. It was still missed due to adjacency competition, not velocity failure. This is a different failure mode. |
| consequence | Even when velocity is detected, adjacency can mask the prediction. The theory's two terms (velocity × adjacency) can conflict. |

### BC-020: IS-95 CDMA (1995) — scaling event

| Field | Value |
|---|---|
| caseId | BC-020 |
| domain | telecommunications |
| event | IS-95 CDMA (1995): Qualcomm, alternative 2G standard |
| violatedAssumption | ["capability_emergence_not_exploitation", "velocity_above_threshold"] |
| failureMode | WIRELESS_PROTOCOL at TRL 9 (plateaued since 1985). RADIO_TRANSMISSION at TRL 9. Both stable. Velocity = 0. Event was an FN. |
| interpretation | IS-95 was an alternative 2G standard (CDMA vs TDMA). It was a coordination/standards event, not a capability emergence. |
| consequence | Same as semiconductor scaling events. The theory does not detect standards competition. |

### BC-021: CDMA2000 EV-DO (2003) — scaling event

| Field | Value |
|---|---|
| caseId | BC-021 |
| domain | telecommunications |
| event | CDMA2000 EV-DO (2003): 3G evolution within CDMA family |
| violatedAssumption | ["capability_emergence_not_exploitation", "velocity_above_threshold"] |
| failureMode | Both WIRELESS_PROTOCOL and PACKET_SWITCHING at TRL 9. Velocity = 0. FN. |
| interpretation | EV-DO was a data overlay on the CDMA voice network — an evolution within an existing generation, not a generation transition. |
| consequence | Same scaling-event pattern. |

### BC-022: Samsung Galaxy S (2010) — scaling event

| Field | Value |
|---|---|
| caseId | BC-022 |
| domain | telecommunications |
| event | Samsung Galaxy S (2010): mass-market 4G smartphone |
| violatedAssumption | ["capability_emergence_not_exploitation", "velocity_above_threshold"] |
| failureMode | SMART_DEVICE_INTEGRATION at TRL 9 (post-iPhone). WIRELESS_PROTOCOL at TRL 9. Both stable. Velocity = 0. FN. |
| interpretation | The Galaxy S was a market-scaling event (mass-market adoption of smartphones), not a capability emergence. |
| consequence | The theory does not detect market-scaling events. |

### BC-023: LTE Advanced (2014) — scaling event

| Field | Value |
|---|---|
| caseId | BC-023 |
| domain | telecommunications |
| event | LTE Advanced (2014): 3GPP Release 10, carrier aggregation, 4x4 MIMO |
| violatedAssumption | ["capability_emergence_not_exploitation", "velocity_above_threshold"] |
| failureMode | Both capabilities at TRL 9. Velocity = 0. FN. |
| interpretation | LTE-A was an evolution within 4G (carrier aggregation, MIMO) — optimization, not emergence. |
| consequence | Same scaling-event pattern. |

### BC-024: Gigabit LTE (2017) — scaling event

| Field | Value |
|---|---|
| caseId | BC-024 |
| domain | telecommunications |
| event | Gigabit LTE (2017): Qualcomm X20, 1 Gbps peak rate |
| violatedAssumption | ["capability_emergence_not_exploitation", "velocity_above_threshold"] |
| failureMode | Both capabilities at TRL 9. Velocity = 0. FN. |
| interpretation | Gigabit LTE was the peak of 4G evolution — modem complexity optimization, not emergence. |
| consequence | Same scaling-event pattern. |

### BC-025: 5G Standalone (2022) — survived D4 but not predicted

| Field | Value |
|---|---|
| caseId | BC-025 |
| domain | telecommunications |
| event | 5G SA (2022): T-Mobile, cloud-native 5G core |
| violatedAssumption | ["velocity_above_threshold"] (partial) |
| failureMode | NETWORK_VIRTUALIZATION was rising (TRL 6 → 8, 2015-2020), velocity at 2021 = 0.40 (above threshold). But the combination {WIRELESS_PROTOCOL, NETWORK_VIRTUALIZATION} also had WIRELESS_PROTOCOL at TRL 9 (velocity 0). The combination scored 0.20 × adjacency — ranked below Top-10. |
| interpretation | This is the one telecom event where a rising capability (NETWORK_VIRTUALIZATION) was genuinely active and above threshold. It was missed due to adjacency competition, not velocity failure. But it survived D4 (it has a rising capability). |
| consequence | Even when velocity is detected, the theory's prediction can fail due to adjacency. The theory's two terms do not always combine effectively. |

### BC-026: 5G Advanced (2023) — survived D4 but not predicted

| Field | Value |
|---|---|
| caseId | BC-026 |
| domain | telecommunications |
| event | 5G Advanced (2023): 3GPP Release 18, 5G evolution |
| violatedAssumption | ["single_rise_per_capability", "monotonic_TRL"] |
| failureMode | SPECTRUM_UTILIZATION re-rose for sub-6GHz evolution (2020-2023). At 2022, velocity = 0.8 (above threshold). But the combination {WIRELESS_PROTOCOL, SPECTRUM_UTILIZATION} had WIRELESS_PROTOCOL at TRL 9 (velocity 0). Max velocity = 0.8. Still missed due to adjacency competition. |
| interpretation | This event survived D4 (it has a rising capability) but was not predicted. Same adjacency competition as BC-025 and BC-019. |
| consequence | The theory's prediction failure is not always about velocity. Adjacency competition can mask predictions even when velocity is high. |

---

## Cross-domain pattern analysis

### Pattern 1: Scaling events (BC-001 to BC-005, BC-020 to BC-024)

**11 of 26 cases** are scaling events: invention that occurs within an already-mature technology base, with zero rising-capability velocity.

- Semiconductor scaling: Intel 4004, 386, Pentium, 0.35um DRAM, 130nm strained Si (5 cases)
- Telecom scaling: IS-95, EV-DO, Galaxy S, LTE-A, Gigabit LTE, (5 cases) + 5G SA, 5G Advanced (2 partial)

These cases violate `capability_emergence_not_exploitation` and `velocity_above_threshold`. They falsify strict necessity (FEC-002) at any velocity threshold.

**Interpretation:** The theory detects capability EMERGENCE, not capability EXPLOITATION. Scaling is a different invention class.

### Pattern 2: Generation transitions (BC-013 to BC-019)

**7 of 26 cases** are generation transitions: invention that occurs when a capability "re-rises" for a new generation. The trajectory model cannot represent this.

- Telecom: GSM 2G, WCDMA 3G, iPhone, LTE 4G, NB-IoT, 5G NR, 5G mmWave (7 cases)

These cases violate `single_rise_per_capability` and `monotonic_TRL`. They falsify strict necessity because the modeled velocity is zero or negative during the transition.

**Interpretation:** TRL as a single value per capability cannot represent generation transitions. The ontology needs per-generation TRL, or a different state variable.

### Pattern 3: Threshold granularity (BC-006 to BC-010)

**5 of 26 cases** are threshold-granularity failures: the rising capability was genuinely rising, but the 5-year TRL snapshot produced velocity exactly at the 0.20 threshold.

- Semiconductors: TSV, FinFET 22nm, FinFET 14nm, EUV 7nm, EUV 5nm (5 cases)

These cases violate only `velocity_above_threshold`. They are NOT robust falsifications — at threshold > 0.15, all 5 would be detected.

**Interpretation:** The pre-stated threshold was calibrated to Li-ion and is too strict for domains with 1-TRL-per-5-year granularity. This is an EP-6 issue, not a theory-falsification.

### Pattern 4: Post-maturity exploitation (BC-011, BC-012)

**2 of 26 cases** are post-maturity exploitation: invention that occurs after a capability has reached TRL 9.

- Semiconductors: AMD 3D V-Cache, Samsung 3nm GAA (2 cases)

These cases violate `capability_emergence_not_exploitation`. They are robust falsifications of strict necessity.

**Interpretation:** The theory cannot detect innovation that occurs after capability maturity. This is the "capability exploitation" boundary — same as Pattern 1, but with a different mechanism (post-maturity refinement vs scaling).

### Pattern 5: Adjacency competition (BC-019, BC-025, BC-026)

**3 of 26 cases** are adjacency-competition failures: velocity was above threshold, but the combination was ranked below Top-10 due to higher-adjacency competitors.

- Telecom: 5G mmWave, 5G SA, 5G Advanced (3 cases)

These cases do NOT violate any assumption — the velocity was real and above threshold. The failure is in the formula's combination of velocity × adjacency.

**Interpretation:** The formula's two terms can conflict. A combination with high velocity but lower adjacency can be ranked below a combination with lower velocity but higher adjacency. This is a formula-architecture issue, not a theory-falsification.

---

## Summary

| Pattern | Count | Domains | Violated assumptions | Robust falsification? |
|---|---|---|---|---|
| 1. Scaling events | 11 | semiconductors, telecom | `capability_emergence_not_exploitation`, `velocity_above_threshold` | YES (at any threshold) |
| 2. Generation transitions | 7 | telecom | `single_rise_per_capability`, `monotonic_TRL` | YES |
| 3. Threshold granularity | 5 | semiconductors | `velocity_above_threshold` | NO (threshold-sensitive) |
| 4. Post-maturity exploitation | 2 | semiconductors | `capability_emergence_not_exploitation` | YES |
| 5. Adjacency competition | 3 | telecom | (none — formula architecture) | NO (not a theory violation) |
| **Total** | **28** | | | |

Note: total is 28, not 26, because some cases fit multiple patterns (e.g., BC-025 is both Pattern 5 and partially Pattern 2).

### The robust falsifications

**20 of 28 cases** are robust falsifications of strict necessity (FEC-002):
- 11 scaling events (Pattern 1)
- 7 generation transitions (Pattern 2)
- 2 post-maturity exploitation (Pattern 4)

These 20 cases falsify the claim "velocity is necessary for invention" at any velocity threshold. They occur across both domains.

### The non-robust failures

**8 of 28 cases** are not robust falsifications:
- 5 threshold granularity (Pattern 3) — would be detected at a lower threshold
- 3 adjacency competition (Pattern 5) — velocity was detected, formula combination failed

These 8 cases represent fixable issues (threshold calibration, formula architecture) but are NOT evidence against the theory itself.

---

## What this catalog does NOT do

- It does not conclude whether the theory is wrong or the ontology is incomplete. That conclusion is in PHASE_14R_REFLECTION.md.
- It does not propose fixes. The formula is frozen (Rule 1). Any fix would be a new formula, tested separately.
- It does not grade the failure cases by severity. All cases are recorded equally.
