# TELECOM_BOTTLENECK_REGISTRY

**Status:** Phase 14A, Domain 2 bottleneck registry.
**Location:** repo root.
**Phase:** 14A.
**Committed before backtest:** yes (per Rule 3).

---

## Schema

```typescript
interface TelecomBottleneck {
    year: number;
    event: string;
    bottleneck: string;
    bottleneckType: "physical" | "manufacturing" | "economic" | "regulatory" | "infrastructure" | "coordination";
    resolution: string;
    yearsToResolve: number;
}
```

Note: added "coordination" as a bottleneck type. This is a
domain-specific extension — telecom's dominant bottleneck is
standards-body consensus (3GPP), which is neither physical,
economic, regulatory, nor infrastructure.

---

## Bottleneck records (1983-2023)

| Year | Event | Bottleneck | Type | Resolution | Years to Resolve |
|---|---|---|---|---|---|
| 1983 | AMPS (1G) | Cellular concept validation (frequency reuse + handoff) | physical | Bell Labs cellular concept (1947) + AMPS standardization (1970s) + FCC spectrum allocation (1981) | 0 (resolved by 1983) |
| 1991 | GSM (2G) | Standards consensus (GSM group formed 1982, needed pan-European standard) | coordination | GSM Memorandum of Understanding (1987) + standard frozen 1990 + spectrum allocation (900MHz) | 0 (resolved by 1991) |
| 1995 | IS-95 CDMA | Standards acceptance (CDMA vs TDMA debate) | coordination | TIA IS-95 standard (1993) + Qualcomm patent licensing | 0 (resolved by 1995) |
| 2001 | WCDMA (3G) | Standards convergence (WCDMA vs CDMA2000) + spectrum (2GHz) | coordination + regulatory | 3GPP formed (1998) + Release 99 frozen (2000) + 2GHz spectrum auctions | 0 (resolved by 2001) |
| 2003 | CDMA2000 EV-DO | Evolution within CDMA family (data overlay on voice network) | coordination | 3GPP2 EV-DO standard (2000) + carrier deployment | 0 (resolved by 2003) |
| 2007 | iPhone | Device hardware (multi-touch, mobile browser, app ecosystem) | manufacturing | Apple iPhone development (2005-2007) + capacitive touch + WebKit | 0 (resolved by 2007) |
| 2009 | LTE (4G) | Standards consensus (LTE vs WiMAX) + all-IP network architecture | coordination + physical | 3GPP Release 8 frozen (2008) + OFDMA + all-IP core | 0 (resolved by 2009) |
| 2010 | Galaxy S | Mass-market smartphone hardware (OLED, 4G modem, app store scale) | manufacturing | Samsung Galaxy S development + Android ecosystem maturity | 0 (resolved by 2010) |
| 2014 | LTE Advanced | Carrier aggregation (multi-band) + 4x4 MIMO | physical | 3GPP Release 10 + RF front-end integration + baseband processing | 0 (resolved by 2014) |
| 2016 | NB-IoT | IoT standards consensus (NB-IoT vs LTE-M vs LoRaWAN) | coordination | 3GPP Release 13 NB-IoT standard (2016) | 0 (resolved by 2016) |
| 2017 | Gigabit LTE | Modem complexity (1 Gbps requires 4x4 MIMO + 256-QAM + 3CA) | physical | Qualcomm X20 modem + RF front-end + baseband | 0 (resolved by 2017) |
| 2019 | 5G NR sub-6GHz | Standards consensus (5G NR NSA vs SA) + mmWave vs sub-6 debate | coordination | 3GPP Release 15 (2018) + sub-6GHz spectrum allocation | 0 (resolved by 2019) |
| 2020 | 5G mmWave | mmWave deployment (range, blockage, power) | physical + infrastructure | mmWave RF front-end + small cell density + beamforming | 2 (partial resolution; ongoing) |
| 2022 | 5G SA | Cloud-native core (5G standalone requires new core, not just radio) | coordination + physical | 3GPP Release 16 + cloud-native core + operators willing to deploy | 0 (resolved by 2022) |
| 2023 | 5G Advanced | 5G evolution (Release 18 features: AI/ML, ambient IoT, network slicing) | coordination | 3GPP Release 18 standard (2023) | 0 (resolved by 2023) |

---

## Bottleneck type distribution

| Type | Count | Events |
|---|---|---|
| coordination | 8 | 1991 GSM, 1995 IS-95, 2001 WCDMA, 2003 EV-DO, 2009 LTE, 2016 NB-IoT, 2019 5G NR, 2022 5G SA |
| physical | 5 | 1983 AMPS, 2014 LTE-A, 2017 Gigabit LTE, 2020 5G mmWave, 2022 5G SA |
| manufacturing | 2 | 2007 iPhone, 2010 Galaxy S |
| regulatory | 1 (partial) | 2001 WCDMA (2GHz spectrum) |
| economic | 0 | — |
| infrastructure | 1 (partial) | 2020 5G mmWave (small cell density) |

**Key observation:** Telecom is dominated by COORDINATION bottlenecks
(8/15, 53%). This is the structural difference from Li-ion (physical
bottlenecks) and semiconductors (physical bottlenecks). Telecom's
main bottleneck is getting 700+ 3GPP member companies to agree on
a standard.

No economic bottlenecks appear — telecom capex is large but not a
binding constraint at the invention level (operators fund new
generations because they must compete).

---

## Bottleneck era analysis

| Era | Dominant bottleneck | Example events |
|---|---|---|
| 1980s | Cellular concept validation (physical) | AMPS (1983): frequency reuse + handoff |
| 1990s | Standards consensus (coordination) | GSM (1991): pan-European standard; IS-95 (1995): CDMA vs TDMA |
| 2000s | Standards convergence + device hardware | WCDMA (2001): 3G convergence; iPhone (2007): smartphone hardware |
| 2010s | Standards evolution + modem complexity | LTE (2009): all-IP; LTE-A (2014): carrier aggregation |
| 2020s | mmWave deployment + cloud-native core | 5G mmWave (2020): range/blockage; 5G SA (2022): cloud core |

---

## Bottleneck resolution timing

| years_to_resolve | Count | Events |
|---|---|---|
| 0 (resolved at event year) | 14 | All except 5G mmWave |
| 2 years | 1 | 2020 5G mmWave (partial) |
| 3+ years | 0 | — |

**Key observation:** 14 of 15 bottlenecks were resolved AT the event
year. This is the same pattern as Li-ion (10/16) and semiconductors
(13/15). Inventions happen at bottleneck resolution — across all
three domains.

---

## What this registry exposes

1. **Coordination is the dominant bottleneck type.** Unlike Li-ion
   (physical/economic) and semiconductors (physical), telecom's
   main bottleneck is standards-body consensus. This is a NEW
   bottleneck type not in the original Li-ion taxonomy. The model's
   CONSTRAINT nodes (per the Li-ion ontology) do not have a
   coordination type.

2. **The coordination bottleneck is invisible to the velocity term.**
   Standards consensus takes 2-3 years (3GPP release cycle), but
   during this time the WIRELESS_PROTOCOL capability is at TRL 5-7
   (pre-commercial). The velocity term sees 0.20-0.40 during
   standardization. But the bottleneck (coordination) is not
   captured — it's a process, not a capability trajectory.

3. **Spectrum allocation is exogenous.** Spectrum auctions are
   regulatory events that unlock deployment. Without spectrum, a
   standard cannot deploy. The model has no concept of regulatory
   events — they're not capabilities, not bottlenecks, not costs.
   This is a structural gap.

4. **The 5G mmWave case (2020) is the only multi-year bottleneck.**
   mmWave deployment has been slow due to range, blockage, and
   small-cell density requirements. This is a 2+ year bottleneck
   that is still partially unresolved. The model's prediction at
   T=2015 should have flagged this as a susceptibility case — but
   the velocity at T=2015 for SPECTRUM_UTILIZATION was NEGATIVE
   (the capability "dropped" to track mmWave), so the model would
   have missed it.
