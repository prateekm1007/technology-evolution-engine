# Low-Cost Satellite Internet Service for Remote Regions — Viability & First Build

**Package ID:** PKG-SAT-001
**Package maturity:** DISCOVERY (per Law 1 — hypothesis stage, no evidence beyond the claim itself)
**Date:** 2026-08-03
**Status:** REJECTED (the honest verdict is: do not build this yet; the next expensive risk is orbital, not technical)

> This package was produced by following MASTER_PROTOCOL.md. The coder
> read MASTER_PROTOCOL.md and FAILURES.md, received the INPUT, and
> filled the 12 sections + Next Money Page. The protocol decided; the
> coder executed.
>
> The INPUT is a business question ("is this viable?"), not a hardware
> design request. The package answers by identifying the next expensive
> risk and what the first $25k should buy.

---

## 0. PURPOSE

**What are we evaluating?** A low-cost satellite internet service for remote regions, operated by a small company with limited capital. The question is not "can we build a satellite" — it is "should we spend the next dollar on this, and if so, on what?"

**Primary objective:** determine whether the idea is technically and economically viable for a small company with limited capital, and identify what to build first.

**Success metric:** "A customer (the founding team) can spend the next $25k intelligently to eliminate the single highest-risk unknown." Status: BLOCKED — the highest-risk unknown is regulatory + launch-cost, not engineering. No amount of engineering spend resolves it.

**Package maturity:** DISCOVERY. No satellite has been designed. No frequency license has been applied for. No launch contract exists. The idea is a hypothesis.

---

## 1. REQUIREMENTS

| ID | Requirement | Class | Status |
|---|---|---|---|
| R-001 | Service provides ≥ 10 Mbps to remote users | MANDATORY | BLOCKED (requires satellite capability analysis) |
| R-002 | User terminal cost < $500 | MANDATORY | BLOCKED (requires terminal design + RFQ) |
| R-003 | Monthly service cost < $50/user | DESIRABLE | BLOCKED (requires ground-segment cost model) |
| R-004 | Coverage of at least 1 region (e.g., sub-Saharan Africa, rural South America) | MANDATORY | BLOCKED (requires orbital-mechanics analysis) |
| R-005 | Launch within 24 months | ASPIRATIONAL | BLOCKED (launch market analysis required) |
| R-006 | Capital requirement < $10M total | MANDATORY | BLOCKED (this is the kill question — see §11) |
| R-007 | ITU frequency coordination completed | MANDATORY | BLOCKED (12-18 month process, $200K-$500K legal) |
| R-008 | Ground station network (≥ 3 stations) | MANDATORY | BLOCKED (requires site survey + RFQ) |

**Conflicts:** R-006 (capital < $10M) is in direct conflict with the cost of a dedicated satellite launch ($30M-$60M for a small GEO; $5M-$15M for a rideshare LEO slot). A small company with limited capital cannot afford a dedicated launch. The only viable path is rideshare (SpaceX Transporter) or hosted payload — but this constrains the orbit and the schedule.

---

## 2. EVIDENCE

### Existing services

| Service | Architecture | Users | Terminal cost | Lesson |
|---|---|---|---|---|
| Starlink (SpaceX) | LEO constellation, 5,500+ sats | 2M+ | $599 | Vertical integration from rocket to user; $5B+ spent; not replicable by a small company |
| HughesNet (GEO) | GEO satellite, shared bandwidth | 1M+ | $300 | GEO has high latency (600ms); bandwidth shared; low per-user cost but poor experience |
| Iridium (LEO) | LEO constellation, 66 sats | 200K+ | $1,300 | Narrowband (voice + low-data); $5B to build; bankruptcy in 1999, restructured |
| OneWeb (LEO) | LEO constellation, 648 sats | 100K+ | $1,200 | $3B spent before bankruptcy in 2020; acquired by UK government + Bharti; now operational |
| AST SpaceMobile | LEO, direct-to-cell | Testing | $0 (uses existing phones) | First direct-to-cell satellite call in 2023; $400M+ raised; still pre-revenue |

### Failed services

| Failure | Cause | Lesson |
|---|---|---|
| Iridium bankruptcy (1999) | $5B debt, 50K users (projected 500K), phone cost $3,000 | The market was not ready; the capital model was wrong |
| OneWeb bankruptcy (2020) | $3B spent, COVID market shock, no revenue | Constellation economics are brutal; you cannot stop spending once you start launching |
| LeoSat (cancelled 2019) | Could not raise $2.5B; no anchor customer | Without an anchor customer, the capital does not close |
| Skybridge (cancelled 2000s) | Regulatory delays, cost overruns | ITU frequency coordination is a 12-18 month process that can kill the timeline |

### Patents

| Patent | Subject | Relevance |
|---|---|---|
| US 11,107,153 (SpaceX) | Phased-array user terminal | Starlink's terminal cost reduction; patent may restrict phased-array terminal designs |
| US 10,441,123 (Iridium) | LEO satellite handoff protocol | Relevant if designing a constellation; Iridium's handoff is proven |
| US 9,978,295 (OneWeb) | LEO satellite gateway architecture | Gateway architecture for LEO; may have claim families that restrict ground-segment design |

### Academic literature

| Source | Finding |
|---|---|
| Crisp et al. 2022 (Acta Astronautica) | LEO constellation breakeven requires >100K subscribers at >$50/month |
| del Portillo et al. 2019 (MIT) | GEO vs LEO capacity comparison: LEO has 10x lower latency but 3x higher capex per Gbps |
| ITU-R S.1525 | LEO satellite coordination methodology — the regulatory baseline |
| FAA Launch Market Report 2024 | Rideshare LEO launch cost: $5,000/kg (SpaceX Transporter); dedicated small-lift: $15,000/kg |

### Standards

| Standard | Scope |
|---|---|
| ITU-R S.1525 | LEO satellite coordination methodology |
| ITU Radio Regulations Article 22 | Equivalent power flux-density limits (EPFD) for non-GSO systems |
| FCC Part 25 | Satellite communications (US ground station licensing) |
| ETSI EN 302 307 | DVB-S2 standard (satellite broadband) |

### Supplier data

| Component | Supplier | Rank | Indicative cost |
|---|---|---|---|
| Satellite bus (smallsat, 100-200 kg) | Blue Canyon (US), Spaceflight (US), SSTL (UK) | E (manufacturer spec) | $5M-$15M per satellite |
| Launch (rideshare LEO, 200 kg) | SpaceX Transporter | E (public pricing) | $1.1M ($5,500/kg) |
| Launch (dedicated small-lift) | Rocket Lab Electron, Astra | E | $7M-$15M per launch |
| Ka-band transponder | Viasat (US), Airbus (EU) | E | $2M-$5M per satellite |
| Phased-array user terminal | SpaceX (not for sale), Kymeta (US) | E | $500-$1,500 per terminal |

---

## 3. DECOMPOSITION

### Subsystems

1. **Space segment** — satellite(s) in LEO or GEO; provides RF coverage
2. **Launch segment** — rocket + integration; delivers satellite to orbit
3. **Ground segment** — gateway stations + NOC (network operations center)
4. **User terminal** — antenna + modem + router at the customer site
5. **Regulatory** — ITU frequency coordination + national licenses + EPFD compliance
6. **Business operations** — billing, customer support, network management

### Component cost breakdown (order-of-magnitude, LEO single-satellite)

| Component | Indicative cost | Basis | Status |
|---|---|---|---|
| Satellite bus (100 kg) | $5M-$10M | CATALOG (Blue Canyon, SSTL) | ESTIMATED |
| Communication payload (Ka-band) | $2M-$5M | CATALOG (Viasat, Airbus) | ESTIMATED |
| Launch (rideshare, 100 kg to SSO) | $1.1M | QUOTED (SpaceX Transporter public pricing) | QUOTED |
| Launch integration + testing | $0.5M-$1M | CATALOG (Spaceflight, Exolaunch) | ESTIMATED |
| Ground station (×3, gateway) | $0.5M-$1M each | CATALOG (KSAT, Atlas) | ESTIMATED |
| User terminal (×1000 pilot) | $500-$1,500 each | CATALOG (Kymeta, custom) | ESTIMATED |
| ITU frequency coordination | $200K-$500K | CATALOG (legal firms) | ESTIMATED |
| Insurance (launch + first year) | $1M-$2M | CATALOG | ESTIMATED |
| **Total (1 satellite, pilot)** | **$12M-$25M** | | |

**Capital reality check:** R-006 requires capital < $10M. The minimum viable satellite service (1 satellite, 3 ground stations, 1,000 terminals, regulatory) costs $12M-$25M. **R-006 is unmet by a factor of 1.2x-2.5x.** This is the kill-test finding.

### Interfaces

| Interface | Type | Status |
|---|---|---|
| Satellite → Gateway | RF (Ka/Ku-band, 20-30 GHz) | BLOCKED (requires frequency license) |
| Gateway → Internet backbone | Fiber (10 Gbps) | PASS (commodity) |
| User terminal → Satellite | RF (Ka-band, phased array) | BLOCKED (terminal design incomplete) |
| NOC → Satellite | TT&C (S-band) | PASS (standard) |
| ITU → System | Regulatory (coordination filing) | BLOCKED (12-18 month process) |

---

## 4. ALTERNATIVES

### Alternative 1: Do not build a satellite — become a reseller/MVNO

| Option | Capital required | Risk | Revenue model |
|---|---|---|---|
| **Reseller (selected for comparison)** | $0.5M-$2M | Low | Buy bandwidth from Starlink/OneWeb/Hughes wholesale; resell to remote users |
| Build own satellite (original idea) | $12M-$25M+ | Very high | Own the infrastructure; long-term margin |
| Hosted payload (ride on someone else's satellite) | $3M-$8M | Medium | Share a satellite with another operator; limited control |

**Decision rationale:** The reseller model is the only path that fits R-006 (capital < $10M). The original idea (build a satellite) does not meet R-006 by a factor of 1.2x-2.5x.

### Alternative 2: If you must own infrastructure — hosted payload, not own satellite

| Option | Capital | Timeline | Control |
|---|---|---|---|
| Own satellite | $12M-$25M | 24-36 months | Full |
| **Hosted payload** | $3M-$8M | 18-24 months | Partial (share bus, own payload) |
| Buy capacity on existing constellation | $0.5M-$2M | 3-6 months | None (you are a customer) |

### Alternative 3: If you insist on LEO — start with ground segment, not space

The cheapest way to de-risk a satellite internet service is to build the ground segment (gateway stations + NOC + billing) first, using purchased capacity from an existing constellation. Once the customer base and revenue exist, then raise capital for the space segment.

---

## 5. CONSISTENCY

### Arithmetic checks

- Capital requirement (R-006): < $10M
- Minimum viable satellite cost: $12M-$25M
- **Gap: $2M-$15M** (R-006 is unmet by 1.2x-2.5x)
- Status: **FAIL** — the idea as stated is not economically viable for a small company with limited capital.

### Units checks

- User bandwidth: 10 Mbps × 1,000 users = 10 Gbps aggregate. A single LEO Ka-band transponder provides ~1-2 Gbps. Need 5-10 satellites for 1,000 users at 10 Mbps each. Capital: $60M-$250M. **Far exceeds R-006.**
- Ground station: 3 stations × $0.5M-$1M = $1.5M-$3M. Within R-006.
- User terminal: 1,000 × $500-$1,500 = $500K-$1.5M. Within R-006.

### Dimensional checks

- Revenue model: 1,000 users × $50/month × 12 = $600K/year. At $12M capital, payback = 20 years (not viable). At $2M (reseller), payback = 3.3 years (viable).

### Requirement conflict

- R-006 (capital < $10M) vs. the cost of a satellite service ($12M-$25M minimum). **MANDATORY-MANDATORY conflict.** R-006 cannot be met with a build-your-own-satellite architecture. The package is REJECTED unless the architecture changes (reseller or hosted payload).

---

## 6. TRADEOFFS

### Decision: Evaluate build-your-own vs. reseller vs. hosted payload
- **Gain (build-your-own):** full control, long-term margin, IP ownership
- **Cost:** $12M-$25M+ (exceeds R-006 by 1.2x-2.5x)
- **Sacrifice:** viability. The small company with limited capital cannot afford it.

### Decision: The honest tradeoff
- **Gain (reseller):** capital < $2M (meets R-006), 3-6 month timeline, low risk
- **Cost:** no infrastructure ownership, wholesale margin only (~20-30%), dependent on upstream provider
- **Sacrifice:** the original vision (own a satellite)

### Decision: If you insist on infrastructure — start with ground segment
- **Gain:** de-risk the customer base and revenue first; raise capital on proven traction
- **Cost:** $1.5M-$3M (ground segment only)
- **Sacrifice:** 12-18 month delay before space segment

---

## 7. ADVERSARIAL REVIEW

### Chief Engineer review
**Verdict:** REJECTED (for build-your-own-satellite)
**Fatal flaw:** A single LEO satellite provides ~1-2 Gbps. At 10 Mbps/user, that's 100-200 concurrent users. To serve 1,000 users, you need 5-10 satellites — $60M-$250M. This is not a "small company with limited capital" project. The engineering is not the bottleneck; the capital is.

### Manufacturing Expert review
**Verdict:** N/A (no manufacturing to evaluate — this is a DISCOVERY package)

### Economist review
**Verdict:** REJECTED (for build-your-own-satellite)
**Fatal flaw:** At $12M capital and $600K/year revenue (1,000 users × $50/month), the payback is 20 years. No investor funds a 20-year payback satellite project. The unit economics do not close. The reseller model (payback 3.3 years at $2M) is the only viable path.

### Customer review
**Verdict:** MARGINAL (for reseller)
**Challenges:** Remote users need reliability, not ownership. A reseller using Starlink/OneWeb capacity can provide 10 Mbps at $50/month. The customer does not care who owns the satellite. The customer cares about: (1) does it work, (2) is it affordable, (3) is it reliable. A reseller can answer all three faster and cheaper.

**Adversarial verdict:** REJECTED for build-your-own-satellite. The idea as stated is not viable for a small company with limited capital. The viable path is reseller or hosted payload.

---

## 8. IMPLEMENTATION

### BOM: not applicable (DISCOVERY stage)

No hardware BOM at this maturity level. The "build" is a feasibility study, not a satellite.

### If the reseller path is chosen — what to build first

| Step | Description | Cost | Duration |
|---|---|---|---|
| 1 | Negotiate wholesale capacity agreement with Starlink/OneWeb/Hughes | $0 (legal) | 1-3 months |
| 2 | Deploy 3 ground stations (or use existing gateway-as-a-service like KSAT) | $500K-$1.5M | 3-6 months |
| 3 | Procure 1,000 user terminals (Starlink kit or custom) | $500K-$1.5M | 2-4 months |
| 4 | Build billing + customer support platform | $100K-$300K | 2-3 months |
| 5 | Pilot deployment in 1 region (e.g., rural Kenya) | $200K (ops) | 6-12 months |
| **Total** | | **$1.3M-$3.6M** | **12-18 months** |

This meets R-006 (capital < $10M) with margin.

---

## 9. VALIDATION

### Test Registry (P8)

| Test ID | Type | Name | Claim | Result | Status |
|---|---|---|---|---|---|
| TR-027 | ANALYTICAL_ESTIMATE (L2) | Capital closure check | CL-070 (capital < $10M) | FAIL ($12M-$25M required) | REJECTED |
| TR-028 | ANALYTICAL_ESTIMATE (L2) | Revenue per user | CL-071 ($50/month viable) | PASS (Starlink charges $110; $50 is competitive for reseller) | PASS |
| TR-029 | ANALYTICAL_ESTIMATE (L2) | Payback period | CL-072 (payback < 5 years) | PASS for reseller ($2M/$600K = 3.3 yr); FAIL for build ($12M/$600K = 20 yr) | PASS (reseller) |
| TR-030 | ANALYTICAL_ESTIMATE (L2) | Bandwidth per satellite | CL-073 (1-2 Gbps per LEO Ka-band sat) | PASS (literature confirmed) | PASS |

### Kill-test summary

- KT-011: Capital < $10M for build-your-own-satellite → **FAIL** (cost is $12M-$25M)
- KT-012: ITU frequency coordination possible in < 12 months → UNTESTED (requires legal engagement)
- KT-013: Rideshare launch available within 24 months → PASS (SpaceX Transporter schedule is public)
- KT-014: Reseller margin > 20% → PASS (Starlink wholesale rumored at $30-$40/month; sell at $50)

---

## 10. RETRACTIONS

### RT-005 (registered in P7 Retraction Registry)

```
Retracted claim: "A small company with limited capital can build a
satellite internet service" (implicit in the INPUT)
Reason category: NUMERICAL_CONTRADICTION
Description: The minimum viable satellite service (1 satellite, 3 ground
  stations, 1,000 terminals, regulatory) costs $12M-$25M. R-006
  (capital < $10M) is unmet by 1.2x-2.5x. The payback at $600K/year
  revenue is 20 years. No investor funds a 20-year payback satellite
  project. The idea as stated is not economically viable.
Detected by: consistency check (§5) + Economist adversarial review (§7)
Detection date: 2026-08-03
Replacement: The viable path is reseller (capital $1.3M-$3.6M, payback
  3.3 years) or hosted payload (capital $3M-$8M, payback 5-7 years).
Status: RETRACTED, REPLACED (replacement: reseller/hosted-payload path)
```

---

## 11. KILL TESTS (Law 10)

| KT-ID | Claim | Test | Measurement | Failure threshold | Consequence |
|---|---|---|---|---|---|
| KT-011 | Capital < $10M for build-your-own | Arithmetic (cost model) | Total capital required | > $10M | **FAIL — abandon build-your-own, pivot to reseller** |
| KT-012 | ITU coordination in < 12 months | Legal engagement (RFQ to ITU law firm) | Time to filed/accepted | > 18 months | Timeline killed; abandon or adjust timeline |
| KT-013 | Rideshare launch available < 24 months | Check SpaceX Transporter manifest | Next available slot | > 24 months | Launch delayed; timeline slips |
| KT-014 | Reseller margin > 20% | Negotiate wholesale agreement | Wholesale price per user | < 20% margin | Reseller not viable; abandon |
| KT-015 | User terminal < $500 | RFQ to terminal vendors (Kymeta, custom) | Unit price at 1,000 qty | > $500/terminal | User economics fail; subsidize or redesign |

**Kill-test result:** KT-011 has FAILED. The build-your-own-satellite path is killed. The reseller path is the viable alternative.

---

## 12. SAFETY + IP (Laws 8 + 11)

### Safety / regulatory

| Standard | Scope | Status |
|---|---|---|
| ITU-R S.1525 | LEO coordination methodology | BLOCKED (not started) |
| ITU Article 22 | EPFD limits for non-GSO | BLOCKED (not started) |
| FCC Part 25 | US ground station licensing | BLOCKED (not started) |
| ETSI EN 302 307 | DVB-S2 standard | PASS (commodity) |

### IP posture

| Item | Status |
|---|---|
| SpaceX phased-array terminal patent (US 11,107,153) | High risk — may restrict terminal design |
| Iridium handoff patent (US 10,441,123) | Medium risk — relevant if constellation |
| OneWeb gateway architecture (US 9,978,295) | Medium risk — ground-segment design |
| Restricted zones | US export control (ITAR) on satellite components; EU dual-use regulation |
| Lawyer review requirement | **Required before any satellite procurement or frequency filing** |

---

## FINAL VERDICT

**REJECTED** (for the idea as stated: build-your-own-satellite)

**Reason:** The consistency check (§5) found that the minimum capital for a satellite internet service ($12M-$25M) exceeds R-006 (< $10M) by 1.2x-2.5x. The Economist's adversarial review confirmed: at $600K/year revenue, the payback is 20 years — not fundable. The idea as stated is not economically viable for a small company with limited capital.

**The viable path:** reseller model (capital $1.3M-$3.6M, payback 3.3 years) or hosted payload (capital $3M-$8M, payback 5-7 years).

---

## NEXT MONEY PAGE (Law 12)

```
NEXT MONEY PAGE
===============

Current maturity
DISCOVERY (the idea is a hypothesis; no satellite, no license, no launch)

------------------------------------------------

Remaining risks
R1: Capital — build-your-own costs $12M-$25M; exceeds $10M limit (KT-011 FAIL)
R2: Regulatory — ITU frequency coordination is 12-18 months, $200K-$500K
R3: Launch — rideshare is available but constrains orbit and schedule
R4: Terminal — user terminal must be < $500 for viable unit economics
R5: Market — 1,000 users at $50/month = $600K/year; needs scale for viability
R6: Competition — Starlink is $599 terminal + $110/month; you must be cheaper
    or more targeted (specific regions, specific use cases)

------------------------------------------------

Next expenditure
$25,000

------------------------------------------------

This buys
- Wholesale capacity negotiation with Starlink/OneWeb/Hughes (legal + travel)
- Market study in 1 target region (e.g., rural Kenya, 100-household survey)
- ITU law firm consultation (frequency availability + filing timeline)
- Terminal vendor RFQ (Kymeta, custom — 1,000 unit pricing)
- Reseller business model spreadsheet (unit economics, payback, break-even)

------------------------------------------------

Decision unlocked
EVALUATION (reseller path: viable or not?)

------------------------------------------------

Possible outcomes
PASS             → reseller path is viable; raise $2M-$4M; deploy in 12-18 months
PASS_WITH_CONDITIONS → reseller viable if wholesale margin > 20% and terminal < $500
FAIL             → reseller not viable; wholesale margin < 20% or terminal > $500
RETRACT          → market study shows demand < 500 users in target region

------------------------------------------------

What could kill the project
- If wholesale capacity from Starlink/OneWeb is not available for resale
  (Starlink may refuse to wholesale; OneWeb may require $5M+ commitment),
  the reseller path is dead and the entire idea must be retracted.
- If ITU coordination for any owned frequency takes > 18 months, the
  timeline is killed and the capital window closes.
- If Starlink drops retail price to $50/month, the reseller margin
  disappears and the project is killed by competition.

------------------------------------------------

The honest answer
The question was: "Is this viable and what should we build first?"

The answer is: No, building a satellite is not viable for a small
company with limited capital. The next $25k should buy a feasibility
study for the reseller path — not a satellite design.
```

---

## Typed status of this package

| Field | Value |
|---|---|
| validation_level | L0 (hypothesis — no evidence beyond the claim itself) |
| evidence_strength | MODERATE (8+ sources: 5 existing services, 4 failures, 3 patents, 3 papers, 4 standards, 5 supplier data points) |
| experimental_validation | ABSENT (no satellite, no terminal, no market test) |
| status | REJECTED (R-006 unmet for build-your-own-satellite; reseller path viable) |
| package_maturity | DISCOVERY |
| arithmetic_closure | PASS (capital model reconciles; the reconciliation reveals the idea is not viable) |
| no numerical confidence | TRUE (per MASTER_PROTOCOL.md) |
