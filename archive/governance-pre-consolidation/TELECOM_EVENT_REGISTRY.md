# TELECOM_EVENT_REGISTRY

**Status:** Phase 14A, Domain 2 event registry.
**Location:** repo root.
**Phase:** 14A.
**Committed before backtest:** yes (per Rule 3).

---

## Schema

```typescript
interface TelecomEvent {
    year: number;
    combination: string[];
    event: string;
    evidence: string[];
    risingCapabilityPresent: boolean;
    group: "A" | "B";  // A = scaling, B = capability-driven
}
```

---

## Events (1983-2023)

### Group A: Scaling / evolution events (no rising capability in combination)

These events are scaling or evolution within an already-mature
generation. The capabilities involved are at TRL 9 at the event
year. These are the destruction test D4 candidates.

| Year | Combination | Event | Evidence | Rising cap? |
|---|---|---|---|---|
| 1995 | [WIRELESS_PROTOCOL, RADIO_TRANSMISSION] | IS-95 CDMA (alternative 2G) | Qualcomm IS-95 standard; 1995 commercial launch in Hong Kong; CDMA as 2G alternative to GSM | No (WIRELESS_PROTOCOL at TRL 9 since 1991) |
| 2003 | [WIRELESS_PROTOCOL, PACKET_SWITCHING] | CDMA2000 EV-DO (3G evolution) | CDMA2000 1xEV-DO Rev. 0 standard; 2003 commercial launch; evolution within CDMA family | No (3G capabilities mature) |
| 2010 | [SMART_DEVICE_INTEGRATION, WIRELESS_PROTOCOL] | Samsung Galaxy S (mass-market 4G smartphone) | Samsung Galaxy S product launch; 2010 global release; mass-market smartphone scaling | No (smartphone capabilities mature) |
| 2014 | [WIRELESS_PROTOCOL, PACKET_SWITCHING] | LTE Advanced (4G evolution) | 3GPP Release 10; 2014 commercial launch; carrier aggregation, 4x4 MIMO | No (4G capabilities mature) |
| 2017 | [WIRELESS_PROTOCOL, SPECTRUM_UTILIZATION] | Gigabit LTE (4G peak) | Qualcomm X20 modem; 2017 commercial; 1 Gbps peak rate; LTE peak evolution | No (4G at peak) |
| 2022 | [WIRELESS_PROTOCOL, NETWORK_VIRTUALIZATION] | 5G Standalone (5G SA) | T-Mobile 5G SA launch 2022-08; 3GPP Release 16; cloud-native 5G core | No (5G NR mature since 2019) |
| 2023 | [WIRELESS_PROTOCOL, SPECTRUM_UTILIZATION] | 5G Advanced (5G evolution) | 3GPP Release 18; 2023 standardization; 5G evolution phase | No (5G mature) |

**7 Group A events** (scaling/evolution within mature generation).

### Group B: Capability-driven events (rising capability present)

These events involve at least one rising capability. The theory
SHOULD predict these.

| Year | Combination | Event | Evidence | Rising cap? |
|---|---|---|---|---|
| 1983 | [WIRELESS_PROTOCOL, RADIO_TRANSMISSION, INFRASTRUCTURE_DEPLOYMENT] | AMPS (1G) commercial launch | AMPS commercial launch in Chicago 1983-10-13; Bell Labs cellular concept (1947); first commercial cellular | Yes (WIRELESS_PROTOCOL rising to TRL 9) |
| 1991 | [WIRELESS_PROTOCOL, RADIO_TRANSMISSION] | GSM (2G) commercial launch | GSM commercial launch in Finland 1991-07; digital cellular standard; first SMS | Yes (WIRELESS_PROTOCOL rising for 2G) |
| 2001 | [WIRELESS_PROTOCOL, PACKET_SWITCHING] | WCDMA (3G) commercial launch | NTT DoCoMo FOMA 3G launch 2001-10; first 3G commercial; packet-switched data | Yes (WIRELESS_PROTOCOL + PACKET_SWITCHING rising for 3G) |
| 2007 | [SMART_DEVICE_INTEGRATION, WIRELESS_PROTOCOL] | iPhone launch | Apple iPhone launch 2007-06; smartphone inflection; multi-touch + mobile internet | Yes (SMART_DEVICE_INTEGRATION rising) |
| 2009 | [WIRELESS_PROTOCOL, PACKET_SWITCHING, SMART_DEVICE_INTEGRATION] | LTE (4G) commercial launch | TeliaSonera LTE launch 2009-12 in Stockholm/Oslo; first 4G commercial; all-IP network | Yes (WIRELESS_PROTOCOL + PACKET_SWITCHING rising for 4G) |
| 2016 | [SMART_DEVICE_INTEGRATION, WIRELESS_PROTOCOL] | NB-IoT standardized | 3GPP Release 13 NB-IoT standard 2016-06; cellular IoT; low-power wide-area | Yes (SMART_DEVICE_INTEGRATION rising for IoT) |
| 2019 | [WIRELESS_PROTOCOL, SPECTRUM_UTILIZATION, NETWORK_VIRTUALIZATION] | 5G NR sub-6GHz commercial | 3GPP Release 15; 2019 commercial launches (Verizon, KT, SKT); first 5G | Yes (WIRELESS_PROTOCOL + SPECTRUM_UTILIZATION rising for 5G) |
| 2020 | [SPECTRUM_UTILIZATION, WIRELESS_PROTOCOL] | 5G mmWave commercial | T-Mobile 5G mmWave 2020; Verizon Ultra Wideband; mmWave deployment | Yes (SPECTRUM_UTILIZATION rising for mmWave) |

**8 Group B events** (capability-driven, rising capability present).

---

## Summary

| Category | Count | Description |
|---|---|---|
| Group A (scaling, no rising cap) | 7 | IS-95, EV-DO, Galaxy S, LTE-A, Gigabit LTE, 5G SA, 5G Advanced |
| Group B (capability-driven, rising cap) | 8 | AMPS, GSM, WCDMA, iPhone, LTE, NB-IoT, 5G NR, 5G mmWave |
| Total | 15 | |

---

## The key structural finding (pre-stated, per EP-4)

The telecom domain has 7/15 events (47%) that occur WITHOUT a
rising capability in the combination. This is HIGHER than
semiconductors (5/15 = 33%). The reason: telecom generations
have LONG maturation periods (each generation is at TRL 9 for
5-10 years before the next generation rises), during which
scaling and evolution events occur.

If destruction test D4 (invention without velocity) uses a strict
falsifier, these 7 events FALSIFY the necessity claim (FEC-002)
for telecom — same as semiconductors.

Additionally, the 8 Group B events involve WIRELESS_PROTOCOL,
which rises in DISCRETE STEPS (each generation is a step from
TRL 3 to TRL 9 over ~5 years, then plateaus). The velocity
threshold of > 0.20 will be at the boundary for these steps
(same granularity issue as semiconductors).

This is pre-stated honestly before the backtest runs.
