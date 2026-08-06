# SUPPLIER_LIBRARY

**Status:** Phase 17 Deliverable 4.
**Location:** repo root.
**Phase:** 17.

---

## Purpose

The Supplier Library catalogues the suppliers for components and
materials. Each supplier has location, cost profile, lead time,
and reliability metrics. This library feeds the Component Library
(supplier IDs) and the Manufacturing Pipeline (supply chain
planning).

---

## Schema

```typescript
interface Supplier {
    id: string
    location: string
    costProfile: number       // [0, 1], 0 = cheapest, 1 = most expensive
    leadTime: number          // weeks for standard order
    reliability: number       // [0, 1], on-time delivery rate
}
```

---

## Supplier catalog

### Electronics suppliers

#### SPL-001: LiDAR supplier (Velodyne / Livox)

| Field | Value |
|---|---|
| id | SPL-001 |
| location | San Jose, CA, USA / Shenzhen, China |
| costProfile | 0.7 |
| leadTime | 6 |
| reliability | 0.85 |
| notes | Velodyne (US, high-end, expensive), Livox (China, cost-effective). Livox Mid-360 used in agricultural robots ($800 vs $4000 for Velodyne). Lead time varies by model. |

#### SPL-002: GPS supplier (Trimble / u-blox)

| Field | Value |
|---|---|
| id | SPL-002 |
| location | Sunnyvale, CA, USA / Thalwil, Switzerland |
| costProfile | 0.6 |
| leadTime | 4 |
| reliability | 0.95 |
| notes | Trimble (agricultural-grade, expensive), u-blox (consumer-grade, affordable). u-blox ZED-F9P is the standard RTK module ($350). High reliability, low lead time. |

#### SPL-003: IMU supplier (Bosch / InvenSense)

| Field | Value |
|---|---|
| id | SPL-003 |
| location | Reutlingen, Germany / San Jose, CA, USA |
| costProfile | 0.3 |
| leadTime | 2 |
| reliability | 0.95 |
| notes | Bosch BMI270 (consumer, $4), InvenSense ICM-42688 ($6). Both widely available. Low cost, low lead time, high reliability. |

#### SPL-004: Camera supplier (Stereolabs / Luxonis)

| Field | Value |
|---|---|
| id | SPL-004 |
| location | Paris, France / Walnut Creek, CA, USA |
| costProfile | 0.6 |
| leadTime | 4 |
| reliability | 0.85 |
| notes | Stereolabs ZED 2i ($450, integrated), Luxonis OAK-D Pro ($300, more flexible). Both provide stereo + AI on-board. Luxonis is more cost-effective for agricultural robots. |

#### SPL-005: Edge AI processor supplier (NVIDIA / NXP)

| Field | Value |
|---|---|
| id | SPL-005 |
| location | Santa Clara, CA, USA / Eindhoven, Netherlands |
| costProfile | 0.7 |
| leadTime | 8 |
| reliability | 0.9 |
| notes | NVIDIA Jetson Orin Nano ($250, 40 TOPS), NXP i.MX 8M Plus ($80, 2 TOPS). NVIDIA is the standard for agricultural robots due to ROS2 support and CUDA ecosystem. Lead time affected by semiconductor cycle. |

### Actuator suppliers

#### SPL-006: Motor supplier (Maxon / Allied Motion)

| Field | Value |
|---|---|
| id | SPL-006 |
| location | Sachseln, Switzerland / Minneapolis, MN, USA |
| costProfile | 0.6 |
| leadTime | 6 |
| reliability | 0.9 |
| notes | Maxon (precision, expensive), Allied Motion (industrial, affordable). 1kW BLDC motors for agricultural robots: Maxon EC-i 40 ($280), Allied Motion Ultraflo ($180). |

### Energy suppliers

#### SPL-007: Battery supplier (CATL / BYD / LG)

| Field | Value |
|---|---|
| id | SPL-007 |
| location | Ningde, China / Shenzhen, China / Seoul, South Korea |
| costProfile | 0.4 |
| leadTime | 8 |
| reliability | 0.85 |
| notes | CATL (largest, lowest cost), BYD (vertical integration), LG (premium). LFP cells: $0.10-0.15/Wh at cell level, $0.30/Wh at pack level with BMS. Lead time affected by EV demand cycle. |

#### SPL-008: Solar panel supplier (Jinko / Trina / First Solar)

| Field | Value |
|---|---|
| id | SPL-008 |
| location | Shangrao, China / Changzhou, China / Tempe, AZ, USA |
| costProfile | 0.3 |
| leadTime | 4 |
| reliability | 0.9 |
| notes | JinkoSolar, Trina Solar (both Chinese, monocrystalline, $0.30/W), First Solar (US, thin-film, different chemistry). 400W panels at $120. Highly commoditized, low lead time. |

### Communications suppliers

#### SPL-009: Cellular module supplier (Quectel / Sierra Wireless)

| Field | Value |
|---|---|
| id | SPL-009 |
| location | Shanghai, China / Richmond, BC, Canada |
| costProfile | 0.3 |
| leadTime | 3 |
| reliability | 0.95 |
| notes | Quectel EC25 ($60, widely used), Sierra Wireless HL7800 ($120, industrial-grade). Quectel is the cost-effective choice for agricultural robots. |

#### SPL-010: LoRaWAN module supplier (Semtech / Murata)

| Field | Value |
|---|---|
| id | SPL-010 |
| location | Camarillo, CA, USA / Kyoto, Japan |
| costProfile | 0.2 |
| leadTime | 2 |
| reliability | 0.95 |
| notes | Semtech SX1276 ($8, reference design), Murata CMWX1ZZABZ ($25, integrated module). Both widely available, low cost. |

### Sensor suppliers

#### SPL-011: Soil moisture supplier (Meter Group / Acclima)

| Field | Value |
|---|---|
| id | SPL-011 |
| location | Pullman, WA, USA / Boise, ID, USA |
| costProfile | 0.6 |
| leadTime | 3 |
| reliability | 0.9 |
| notes | Meter Group Teros 10 ($45, capacitive), Acclima TDR-310H ($180, TDR). Capacitive is sufficient for most agricultural robots. |

#### SPL-012: Multispectral camera supplier (MicaSense / Sentera)

| Field | Value |
|---|---|
| id | SPL-012 |
| location | Seattle, WA, USA / Minneapolis, MN, USA |
| costProfile | 0.7 |
| leadTime | 4 |
| reliability | 0.85 |
| notes | MicaSense RedEdge-MX ($500, 5-band), Sentera 6X ($2000, 6-band). MicaSense is the standard for agricultural NDVI. |

### Processor suppliers

#### SPL-013: Microcontroller supplier (STMicro / NXP)

| Field | Value |
|---|---|
| id | SPL-013 |
| location | Geneva, Switzerland / Eindhoven, Netherlands |
| costProfile | 0.2 |
| leadTime | 4 |
| reliability | 0.95 |
| notes | STM32H7 ($15, ARM Cortex-M7), NXP i.MX RT1170 ($12, crossover). Both widely available, low cost. |

### Material suppliers

#### SPL-014: Aluminum supplier (Novelis / Hydro)

| Field | Value |
|---|---|
| id | SPL-014 |
| location | Atlanta, GA, USA / Oslo, Norway |
| costProfile | 0.3 |
| leadTime | 3 |
| reliability | 0.95 |
| notes | Novelis (rolled aluminum sheet/plate), Norsk Hydro (extrusions). Both global suppliers, $4.50/kg for 6061-T6. Highly commoditized. |

#### SPL-015: Silicon wafer supplier (SUMCO / GlobalWafers)

| Field | Value |
|---|---|
| id | SPL-015 |
| location | Tokyo, Japan / Hsinchu, Taiwan |
| costProfile | 0.5 |
| leadTime | 12 |
| reliability | 0.9 |
| notes | SUMCO (Japan, 20% market share), GlobalWafers (Taiwan, 15%). Wafer-grade silicon at $50/kg. Long lead time due to semiconductor cycle. |

#### SPL-016: Copper supplier (Freeport-McMoRan / Codelco)

| Field | Value |
|---|---|
| id | SPL-016 |
| location | Phoenix, AZ, USA / Santiago, Chile |
| costProfile | 0.4 |
| leadTime | 4 |
| reliability | 0.9 |
| notes | Freeport-McMoRan (US, copper mining), Codelco (Chile, state-owned). Copper at $9/kg. Price volatile with commodity cycle. |

#### SPL-017: LFP cathode supplier (Umicore / Posco / BASF)

| Field | Value |
|---|---|
| id | SPL-017 |
| location | Brussels, Belgium / Pohang, South Korea / Ludwigshafen, Germany |
| costProfile | 0.5 |
| leadTime | 8 |
| reliability | 0.85 |
| notes | Umicore (Belgium, integrated cathode producer), Posco (Korea, vertical integration), BASF (Germany, cathode materials). LFP cathode powder at $25/kg. |

#### SPL-018: Polymer supplier (SABIC / BASF / Covestro)

| Field | Value |
|---|---|
| id | SPL-018 |
| location | Riyadh, Saudi Arabia / Ludwigshafen, Germany / Leverkusen, Germany |
| costProfile | 0.3 |
| leadTime | 3 |
| reliability | 0.95 |
| notes | SABIC (ABS/PC blends), BASF (engineering plastics), Covestro (polycarbonate). ABS/PC blend at $3.50/kg. Highly available. |

#### SPL-019: Carbon fiber supplier (Toray / Hexcel)

| Field | Value |
|---|---|
| id | SPL-019 |
| location | Tokyo, Japan / Stamford, CT, USA |
| costProfile | 0.8 |
| leadTime | 8 |
| reliability | 0.85 |
| notes | Toray (Japan, 35% market share), Hexcel (US, aerospace-grade). T300 prepreg at $35/kg. Expensive, used selectively. |

#### SPL-020: Steel supplier (Nucor / ArcelorMittal)

| Field | Value |
|---|---|
| id | SPL-020 |
| location | Charlotte, NC, USA / Luxembourg |
| costProfile | 0.2 |
| leadTime | 2 |
| reliability | 0.95 |
| notes | Nucor (US, mini-mill), ArcelorMittal (global, integrated). 1018 cold-rolled steel at $1.20/kg. Highly commoditized. |

---

## Supplier summary

| ID | Category | Cost profile | Lead time (weeks) | Reliability |
|---|---|---|---|---|
| SPL-001 | LiDAR | 0.7 | 6 | 0.85 |
| SPL-002 | GPS | 0.6 | 4 | 0.95 |
| SPL-003 | IMU | 0.3 | 2 | 0.95 |
| SPL-004 | Camera | 0.6 | 4 | 0.85 |
| SPL-005 | Edge AI | 0.7 | 8 | 0.9 |
| SPL-006 | Motor | 0.6 | 6 | 0.9 |
| SPL-007 | Battery | 0.4 | 8 | 0.85 |
| SPL-008 | Solar | 0.3 | 4 | 0.9 |
| SPL-009 | Cellular | 0.3 | 3 | 0.95 |
| SPL-010 | LoRaWAN | 0.2 | 2 | 0.95 |
| SPL-011 | Soil sensor | 0.6 | 3 | 0.9 |
| SPL-012 | Multispectral | 0.7 | 4 | 0.85 |
| SPL-013 | MCU | 0.2 | 4 | 0.95 |
| SPL-014 | Aluminum | 0.3 | 3 | 0.95 |
| SPL-015 | Silicon | 0.5 | 12 | 0.9 |
| SPL-016 | Copper | 0.4 | 4 | 0.9 |
| SPL-017 | LFP cathode | 0.5 | 8 | 0.85 |
| SPL-018 | Polymer | 0.3 | 3 | 0.95 |
| SPL-019 | Carbon fiber | 0.8 | 8 | 0.85 |
| SPL-020 | Steel | 0.2 | 2 | 0.95 |

---

## What this library does NOT do

- It does not guarantee supplier availability. Suppliers and prices change.
- It does not model supplier relationships (volume discounts, exclusivity).
- It does not include logistics (shipping costs, customs, duties).
- It does not modify the frozen formula or any prior architecture.

---

## Pre-stated falsifier (EP-4)

**Claim:** The 20 suppliers in this library are sufficient to source all components and materials in the Component and Material libraries.

**Falsifier:** A component or material that requires a supplier not in this library — e.g., a rare-earth magnet supplier (neodymium), or a PCB manufacturer.

**Status:** PENDING. The example blueprint will test this.
