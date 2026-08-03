# TELECOM_ONTOLOGY

**Status:** Phase 14A, Domain 2 capability ontology.
**Location:** repo root.
**Phase:** 14A.
**Committed before backtest:** yes (per Rule 3).

> You are transferring the methodology, not the ontology.
> — CEO directive, Phase 14, Rule 2

---

## Purpose

This document defines the capability ontology for the telecommunications
domain. It is committed BEFORE the backtest runs (per Rule 3). It
cannot be modified after the backtest commits (Law 7).

The ontology transfers the METHODOLOGY (capability + trajectory +
adjacency + frozen formula), not the semiconductor or Li-ion
ontology. The telecom capabilities are domain-specific.

---

## The four invariant questions (per INVARIANT_REGISTRY.md)

### What accumulates?

Protocol generation count (1G → 2G → 3G → 4G → 5G → 6G). Each
generation adds to the historical accumulation — old generations
don't disappear, they coexist with new ones during transition
periods (e.g., 2G and 3G both operated in 2010).

Spectrum utilization efficiency (bits/Hz) also accumulates: each
generation uses spectrum more efficiently than the last.

### What accelerates?

3GPP release cycles (every 1-2 years for major releases). Each
release freezes a new standard, which then takes 3-5 years to
reach commercial deployment. The release cycle IS the accelerator
— it's the clock that drives generation transitions.

### What constrains?

Standards-body consensus (coordination bottleneck, not physical).
3GPP has 700+ member companies; consensus on a release takes 2-3
years. This is the dominant bottleneck — it's why telecom moves
in 10-year generation cycles rather than continuously.

Secondary: spectrum availability (regulatory). Spectrum auctions
are exogenous regulatory events that unlock deployment. Without
spectrum allocation, a standard cannot deploy.

Tertiary: infrastructure deployment cost (economic: cell tower
density). A new generation requires new base stations; the capex
cycle is 5-7 years.

### What becomes adjacent?

New use cases become reachable at each generation:
- 2G: SMS, basic data (1991)
- 3G: mobile internet, video (2001)
- 4G: streaming video, mobile apps (2009)
- 5G: IoT, low-latency, fixed wireless access (2019)
- 6G (anticipated): holographic communication, sensing (2030+)

Each generation enables 2-3 new combination classes. The
adjacent-possibility expansion happens AT generation transitions,
not continuously.

---

## Capability list (8 capabilities)

### Rising capabilities (5)

These capabilities rise from low TRL to TRL 9 during the 1975-2025
window. They are the telecom analog of semiconductors' rising
capabilities.

#### 1. WIRELESS_PROTOCOL

The capability of implementing wireless communication protocols
at the state of the art. Each generation (1G, 2G, 3G, 4G, 5G, 6G)
is a step-rise in this capability — not a smooth trajectory.

- 1G concept: 1970s (Bell Labs cellular concept)
- 1G commercial: 1983 (AMPS)
- 2G concept: 1982 (GSM group formed)
- 2G commercial: 1991 (GSM)
- 3G concept: 1996 (3GPP formed)
- 3G commercial: 2001 (WCDMA)
- 4G concept: 2004 (LTE work started)
- 4G commercial: 2009 (LTE)
- 5G concept: 2012 (5G PPP formed)
- 5G commercial: 2019 (5G NR)
- 6G concept: 2019 (research begins)

#### 2. SPECTRUM_UTILIZATION

The capability of using radio spectrum efficiently, including
higher-frequency bands. Rises as the industry moves from low-band
(sub-1GHz) to mid-band (2-6GHz) to mmWave (24-100GHz).

- Sub-1GHz: mature since 1980s
- 2-6GHz: 3G/4G era (2000s)
- mmWave: 5G era (2019+)
- Sub-THz: 6G research (2025+)

#### 3. PACKET_SWITCHING

The capability of IP-based networking for mobile networks. Rises
as the network core moves from circuit-switched (1G/2G) to
packet-switched (3G) to all-IP (4G/5G).

- Circuit-switched: mature since 1980s
- Packet-switched core: 3G era (2001+)
- All-IP: 4G era (2009+)
- Software-defined: 5G SA (2022+)

#### 4. SMART_DEVICE_INTEGRATION

The capability of integrating wireless connectivity into smart
devices (smartphones, IoT devices). Rises as device form factors
evolve.

- Basic phone: mature since 1980s
- Feature phone: 1990s
- Smartphone: 2007+ (iPhone)
- IoT device: 2015+ (NB-IoT, LTE-M)
- AR/VR device: 2020+ (still emerging)

#### 5. NETWORK_VIRTUALIZATION

The capability of software-defined networking (SDN) and network
function virtualization (NFV). Rises as the network core moves
from hardware appliances to software running on commodity servers.

- Concept: 2000s (OpenFlow, SDN research)
- Lab: 2010s (NFV PoC)
- Pilot: 2015 (early 5G cloud RAN)
- Production: 2020+ (5G SA with cloud-native core)
- Mature: still maturing (2025)

### Stable base capabilities (3)

#### 6. RADIO_TRANSMISSION

The capability of RF transmission itself. At TRL 9 since the
1900s (Marconi). This is the most mature capability in any
domain the project has tracked.

#### 7. ANTENNA_HARDWARE

The capability of building physical antennas. At TRL 9 since
the 1930s. Note: advanced antenna techniques (MIMO, beamforming)
are subsumed under SPECTRUM_UTILIZATION, not here.

#### 8. INFRASTRUCTURE_DEPLOYMENT

The capability of deploying and operating cell site infrastructure.
At TRL 9 since the 1980s (when cellular networks first deployed
at scale). Cell site construction, backhaul, power, and maintenance
are all mature capabilities.

---

## Why 8 capabilities

Same count as semiconductors (5 rising, 3 stable). The telecom
domain has MORE rising capabilities than Li-ion (which had 3)
because, like semiconductors, telecom is defined by successive
technology generations.

---

## What this ontology does NOT include

- **STANDARDS_CONSENSUS.** Excluded because it's a process
  (coordination), not a capability. The coordination bottleneck
  is tracked in TELECOM_BOTTLENECK_REGISTRY.md.
- **SPECTRUM_ALLOCATION.** Excluded because it's a regulatory
  event, not a capability. Spectrum auctions are exogenous
  shocks tracked in the bottleneck registry.
- **BILLING_AND_OSS.** Excluded because operational support
  systems are infrastructure, not invention-relevant capability.
- **DEVICE_HARDWARE (CPU, display, battery).** Excluded because
  these are semiconductor-domain capabilities, not telecom.

---

## The structural violation (per INVARIANT_REGISTRY.md)

Telecom violates Li-ion's assumptions in three ways:

1. **TRL is discrete by generation, not continuous.** WIRELESS_PROTOCOL
   rises in steps (each generation is a step from TRL 3 to TRL 9),
   then plateaus, then the next generation rises. This is different
   from Li-ion (smooth TRL rise) and similar to semiconductors
   (lithography generations).

2. **The bottleneck is coordination (3GPP consensus), not physical
   or economic.** Li-ion's bottlenecks were physical (thermal
   runaway) or economic (cost per kWh). Telecom's bottleneck is
   coordination — getting 700+ companies to agree on a standard.
   This is not captured in the capability ontology.

3. **Multi-capability simultaneity required.** A protocol is useless
   without device ecosystem and infrastructure deployment. Invention
   requires WIRELESS_PROTOCOL + SMART_DEVICE_INTEGRATION +
   INFRASTRUCTURE_DEPLOYMENT all at TRL ≥ 7 simultaneously. Li-ion
   did not require this simultaneity (a single rising capability
   was sufficient).

These violations are pre-stated. The backtest will reveal whether
the frozen formula (calibrated to Li-ion's smooth trajectories)
can handle telecom's step-wise progression and coordination
bottlenecks.

---

## Enforcement

- This ontology is frozen once committed. It cannot be modified
  after the backtest runs (Law 7).
- If the backtest reveals a missing capability, it is noted but
  the backtest is NOT re-run.
- The TRL trajectories are in TELECOM_TRAJECTORY_REGISTRY.md.
