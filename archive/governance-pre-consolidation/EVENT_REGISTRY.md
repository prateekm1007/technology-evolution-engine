# EVENT_REGISTRY — Phase 11B

**Status:** evidence layer (historical events registry).
**Location:** repo root.
**Phase:** 11B.

## Schema

```typescript
interface HistoricalEvent {
    year: number;
    combination: string[];
    event: string;
    evidence: string[];
    significance: string;
}
```

## Li-ion intercalation events (1991-2023)

| Year | Combination | Event | Evidence | Significance |
|---|---|---|---|---|
| 1991 | [ELECTROCHEMICAL_ENERGY_STORAGE, ION_TRANSPORT, INTERCALATION] | Sony commercializes first Li-ion cell | Sony press release; Goodenough's LCO cathode (1980); Yoshino's prototype (1985) | First commercial Li-ion. Proves electrochemical storage via intercalation is viable. |
| 1992 | [ELECTROCHEMICAL_ENERGY_STORAGE, INTERCALATION, CELL_ASSEMBLY] | Li-ion in consumer electronics (camcorders) | Sony CCD-TR1 camcorder; industry reports | First consumer product. Mass manufacturing begins. |
| 1996 | [ELECTROCHEMICAL_ENERGY_STORAGE, INTERCALATION, ELECTRODE_COATING] | LFP cathode commercialization (Goodenough, UT Austin) | Goodenough & Kim, US Patent 5,910,382; A123 Systems founded 2001 | New cathode chemistry expands material options. LFP becomes dominant in power tools and later EVs. |
| 1997 | [ELECTROCHEMICAL_ENERGY_STORAGE, INTERCALATION, STATE_OF_CHARGE_MONITORING] | Li-ion with BMS in early EVs (Nissan Altra, Toyota RAV4 EV) | Nissan Altra EV specs; Toyota RAV4 EV documentation | First Li-ion EVs. BMS becomes essential for multi-cell packs. |
| 2001 | [ELECTROCHEMICAL_ENERGY_STORAGE, INTERCALATION, ELECTRON_COLLECTION] | NCM cathode (Argonne National Lab) | Argonne patent US 6,677,082; Thackeray et al. | Layered oxide cathodes with higher energy density. Enables longer-range EVs. |
| 2003 | [ELECTROCHEMICAL_ENERGY_STORAGE, THERMAL_MANAGEMENT, SAFETY_PROTECTION] | Tesla Motors founded; begins Roadster development | Tesla founding documents; press coverage | First company to bet on Li-ion for performance EVs. Pushes thermal management and safety requirements. |
| 2004 | [ELECTROCHEMICAL_ENERGY_STORAGE, INTERCALATION, ELECTRON_COLLECTION] | NCM cathode commercialization | Argonne licensing to BASF, BMZ; industry adoption | NCM enters mass production. Becomes dominant EV cathode chemistry. |
| 2008 | [ELECTROCHEMICAL_ENERGY_STORAGE, THERMAL_MANAGEMENT, STATE_OF_CHARGE_MONITORING] | Tesla Roadster production begins | Tesla Roadster specs; ~2,500 units sold 2008-2012 | First production Li-ion EV with active thermal management + BMS. Proves Li-ion EVs can be desirable. |
| 2010 | [ELECTROCHEMICAL_ENERGY_STORAGE, FAST_CHARGING, THERMAL_MANAGEMENT, SAFETY_PROTECTION] | Mass-market Li-ion EVs (Nissan Leaf, Chevy Volt) | Nissan Leaf launch; Chevy Volt launch; EPA ratings | First mass-market Li-ion EVs. Fast charging becomes a consumer expectation. |
| 2012 | [FAST_CHARGING, THERMAL_MANAGEMENT] | Tesla Supercharger network launches | Tesla press release; Supercharger locations | First DC fast charging network. Changes the EV charging paradigm. |
| 2013 | [ELECTROCHEMICAL_ENERGY_STORAGE, STATE_OF_CHARGE_MONITORING, SAFETY_PROTECTION] | Boeing 787 Li-ion battery fires | NTSB reports; FAA airworthiness directives | Safety incident. Highlights thermal runaway risk in Li-ion packs. Drives safety protection improvements. |
| 2016 | [ELECTROCHEMICAL_ENERGY_STORAGE, ELECTRODE_COATING, CELL_ASSEMBLY] | Tesla Gigafactory begins production | Tesla Gigafactory announcement; production data | First battery Gigafactory. Mass manufacturing at unprecedented scale. |
| 2017 | [ELECTROCHEMICAL_ENERGY_STORAGE, INTERCALATION, ELECTRON_COLLECTION] | NMC 811 cathode (high nickel) | CATL, LG Chem, SK Innovation announcements | Push to high-nickel cathodes for higher energy density. Cost-Driven chemistry shift. |
| 2019 | [FAST_CHARGING, THERMAL_MANAGEMENT, SAFETY_PROTECTION] | Porsche Taycan 800V fast-charging architecture | Porsche Taycan specs; 800V charging demonstrations | First 800V EV architecture. Enables 350kW fast charging. Pushes thermal management to new limits. |
| 2020 | [ELECTROCHEMICAL_ENERGY_STORAGE, ELECTRODE_COATING, CELL_ASSEMBLY] | Tesla 4680 cell announced (Battery Day) | Tesla Battery Day presentation; 4680 specs | Tabless cell design. New manufacturing approach. Structural battery pack. |
| 2023 | [ELECTROCHEMICAL_ENERGY_STORAGE, FAST_CHARGING, THERMAL_MANAGEMENT] | 4C fast charging becomes mainstream (CATL Shenxing, BYD Blade) | CATL Shenxing announcement; BYD Blade 2.0 | 4C charging (15 min to 80%) becomes commercially available. LFP chemistry achieves fast charging. |

## Notes

- 16 events spanning 1991-2023.
- Each event records the capability combination that was newly
  realized or significantly advanced.
- Evidence cites specific sources (patents, press releases, reports).
- Significance explains why the event matters for the model.
