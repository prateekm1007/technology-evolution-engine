# COMPONENT_LIBRARY

**Status:** Phase 17 Deliverable 2.
**Location:** repo root.
**Phase:** 17.

---

## Purpose

The Component Library is the catalog of physical and logical
components that can be assembled into an agricultural robot. Each
component has a unique ID, real-world specifications, and
references to suppliers and materials. This library is the
foundation for COMPONENT_ENGINE.md (Phase 16A).

---

## Schema

```typescript
interface Component {
    id: string
    name: string
    description: string
    maturity: number          // [0, 1], TRL/9
    dependencies: string[]    // other component IDs
    alternatives: string[]     // other component IDs
    category: string           // e.g., "sensor", "actuator", "processor"
    supplier: string           // supplier ID from SUPPLIER_LIBRARY.md
    material: string           // material ID from MATERIAL_LIBRARY.md
    cost: number               // USD at quantity 1000
    weight: number             // kg
    powerDraw: number          // W
    specs: Record<string, number | string>  // component-specific specs
}
```

---

## Component catalog

### Sensors

#### CMP-001: LiDAR (3D scanning)

| Field | Value |
|---|---|
| id | CMP-001 |
| name | LiDAR (3D scanning) |
| description | Solid-state 3D LiDAR for obstacle detection and navigation |
| maturity | 0.85 |
| dependencies | ["CMP-005"] |
| alternatives | ["CMP-001a (stereo camera only)"] |
| category | sensor |
| supplier | SPL-001 (Velodyne / Livox) |
| material | MAT-001 (aluminum housing) |
| cost | 800 |
| weight | 0.5 |
| powerDraw | 8 |
| specs | {range_m: 100, resolution_deg: 0.2, scan_rate_Hz: 20, ip_rating: "IP67"} |

#### CMP-002: GPS (RTK)

| Field | Value |
|---|---|
| id | CMP-002 |
| name | GPS (RTK) |
| description | Real-Time Kinematic GPS module for centimeter-level positioning |
| maturity | 0.95 |
| dependencies | [] |
| alternatives | ["CMP-002a (visual odometry)"] |
| category | sensor |
| supplier | SPL-002 (Trimble / u-blox) |
| material | MAT-001 (aluminum housing) |
| cost | 350 |
| weight | 0.1 |
| powerDraw | 2 |
| specs | {accuracy_m: 0.025, update_rate_Hz: 10, channels: 72, ntrip_required: true} |

#### CMP-003: IMU (6-axis)

| Field | Value |
|---|---|
| id | CMP-003 |
| name | IMU (6-axis) |
| description | 6-axis inertial measurement unit (3-axis accelerometer + 3-axis gyroscope) |
| maturity | 0.95 |
| dependencies | [] |
| alternatives | ["CMP-003a (9-axis with magnetometer)"] |
| category | sensor |
| supplier | SPL-003 (Bosch / InvenSense) |
| material | MAT-002 (silicon) |
| cost | 25 |
| weight | 0.005 |
| powerDraw | 0.01 |
| specs | {accel_range_g: 16, gyro_range_dps: 2000, noise_density: 0.01} |

#### CMP-004: Camera (stereo, global shutter)

| Field | Value |
|---|---|
| id | CMP-004 |
| name | Camera (stereo, global shutter) |
| description | Stereo camera pair with global shutter for vision-based navigation and crop detection |
| maturity | 0.85 |
| dependencies | ["CMP-005"] |
| alternatives | ["CMP-001 (LiDAR only)"] |
| category | sensor |
| supplier | SPL-004 (Stereolabs / Luxonis) |
| material | MAT-001 (aluminum housing) |
| cost | 300 |
| weight | 0.2 |
| powerDraw | 3 |
| specs | {resolution_MP: 4, baseline_mm: 120, fps: 60, ip_rating: "IP65"} |

### Processors

#### CMP-005: Edge AI Processor

| Field | Value |
|---|---|
| id | CMP-005 |
| name | Edge AI Processor |
| description | ARM-based edge computing module with AI acceleration for real-time navigation and crop detection |
| maturity | 0.9 |
| dependencies | ["CMP-006"] |
| alternatives | ["CMP-005a (Raspberry Pi 5 + Coral USB)"] |
| category | processor |
| supplier | SPL-005 (NVIDIA / NXP) |
| material | MAT-002 (silicon) |
| cost | 250 |
| weight | 0.15 |
| powerDraw | 15 |
| specs | {cpu_cores: 6, ram_gb: 8, ai_tops: 40, os: "Ubuntu 22.04 + ROS2"} |

### Actuators

#### CMP-006: Brushless DC Motor (1kW)

| Field | Value |
|---|---|
| id | CMP-006 |
| name | Brushless DC Motor (1kW) |
| description | 1kW brushless DC motor for locomotion and implement actuation |
| maturity | 0.95 |
| dependencies | [] |
| alternatives | ["CMP-006a (stepper motor)"] |
| category | actuator |
| supplier | SPL-006 (Maxon / Allied Motion) |
| material | MAT-001 (aluminum), MAT-003 (copper windings) |
| cost | 180 |
| weight | 2.5 |
| powerDraw | 1000 |
| specs | {rated_power_W: 1000, rated_torque_Nm: 8, max_rpm: 3000, efficiency_pct: 92} |

### Energy

#### CMP-007: Li-ion Battery Pack (LFP, 2kWh)

| Field | Value |
|---|---|
| id | CMP-007 |
| name | Li-ion Battery Pack (LFP, 2kWh) |
| description | Lithium iron phosphate battery pack with BMS, 48V nominal, 2kWh capacity |
| maturity | 0.95 |
| dependencies | [] |
| alternatives | ["CMP-007a (lead-acid, cheaper but heavier)"] |
| category | energy |
| supplier | SPL-007 (CATL / BYD / LG) |
| material | MAT-004 (lithium), MAT-003 (copper), MAT-005 (polymer) |
| cost | 600 |
| weight | 18 |
| powerDraw | -500 (source, not draw) |
| specs | {chemistry: "LFP", voltage_V: 48, capacity_kWh: 2, cycles: 4000, ip_rating: "IP67"} |

#### CMP-008: Solar Panel (400W monocrystalline)

| Field | Value |
|---|---|
| id | CMP-008 |
| name | Solar Panel (400W monocrystalline) |
| description | 400W monocrystalline solar panel for charging batteries during operation |
| maturity | 0.95 |
| dependencies | [] |
| alternatives | ["CMP-008a (flexible thin-film, lower efficiency)"] |
| category | energy |
| supplier | SPL-008 (Jinko / Trina / First Solar) |
| material | MAT-002 (silicon), MAT-001 (aluminum frame) |
| cost | 120 |
| weight | 22 |
| powerDraw | -400 (source, not draw) |
| specs | {rated_power_W: 400, efficiency_pct: 21, area_m2: 2, temperature_coefficient: -0.35} |

### Communications

#### CMP-009: 4G LTE Module

| Field | Value |
|---|---|
| id | CMP-009 |
| name | 4G LTE Module |
| description | 4G LTE cellular module for remote monitoring and fleet coordination |
| maturity | 0.95 |
| dependencies | [] |
| alternatives | ["CMP-009a (5G module, higher cost)"] |
| category | communications |
| supplier | SPL-009 (Quectel / Sierra Wireless) |
| material | MAT-002 (silicon) |
| cost | 60 |
| weight | 0.05 |
| powerDraw | 2 |
| specs | {bands: "global", max_downlink_mbps: 150, max_uplink_mbps: 50, gps_integrated: true} |

#### CMP-010: LoRaWAN Module

| Field | Value |
|---|---|
| id | CMP-010 |
| name | LoRaWAN Module |
| description | LoRaWAN module for low-bandwidth backup communication in areas without cellular coverage |
| maturity | 0.9 |
| dependencies | [] |
| alternatives | ["CMP-010a (satellite module, higher cost)"] |
| category | communications |
| supplier | SPL-010 (Semtech / Murata) |
| material | MAT-002 (silicon) |
| cost | 25 |
| weight | 0.01 |
| powerDraw | 0.1 |
| specs | {frequency_MHz: 915, range_km: 15, data_rate_kbps: 50, power_mw: 100} |

### Environmental sensors

#### CMP-011: Soil Moisture Sensor

| Field | Value |
|---|---|
| id | CMP-011 |
| name | Soil Moisture Sensor |
| description | Capacitive soil moisture sensor for irrigation decision-making |
| maturity | 0.9 |
| dependencies | ["CMP-005"] |
| alternatives | ["CMP-011a (time-domain reflectometry, more accurate)"] |
| category | sensor |
| supplier | SPL-011 (Meter Group / Acclima) |
| material | MAT-005 (polymer) |
| cost | 45 |
| weight | 0.1 |
| powerDraw | 0.05 |
| specs | {measurement_range_pct: 0-100, accuracy_pct: 3, depth_cm: 30, response_time_s: 1} |

#### CMP-012: Multispectral Camera (NDVI)

| Field | Value |
|---|---|
| id | CMP-012 |
| name | Multispectral Camera (NDVI) |
| description | 5-band multispectral camera for crop health assessment (NDVI calculation) |
| maturity | 0.8 |
| dependencies | ["CMP-005"] |
| alternatives | ["CMP-012a (satellite imagery, lower resolution)"] |
| category | sensor |
| supplier | SPL-012 (MicaSense / Sentera) |
| material | MAT-001 (aluminum), MAT-002 (silicon sensor) |
| cost | 500 |
| weight | 0.15 |
| powerDraw | 2 |
| specs | {bands: 5, resolution_MP: 5, fps: 1, ground_resolution_cm: 5, ip_rating: "IP65"} |

### Structural

#### CMP-013: Microcontroller (real-time control)

| Field | Value |
|---|---|
| id | CMP-013 |
| name | Microcontroller (real-time control) |
| description | Real-time microcontroller for motor control and sensor polling |
| maturity | 0.95 |
| dependencies | [] |
| alternatives | ["CMP-013a (FPGA, more flexible)"] |
| category | processor |
| supplier | SPL-013 (STMicro / NXP) |
| material | MAT-002 (silicon) |
| cost | 15 |
| weight | 0.01 |
| powerDraw | 0.5 |
| specs | {architecture: "ARM Cortex-M7", clock_MHz: 480, ram_kb: 512, peripherals: "CAN, PWM, ADC"} |

---

## Component summary

| Category | Components | Count |
|---|---|---|
| Sensor | CMP-001 (LiDAR), CMP-002 (GPS), CMP-003 (IMU), CMP-004 (Camera), CMP-011 (Soil), CMP-012 (Multispectral) | 6 |
| Processor | CMP-005 (Edge AI), CMP-013 (MCU) | 2 |
| Actuator | CMP-006 (BLDC Motor) | 1 |
| Energy | CMP-007 (Battery), CMP-008 (Solar) | 2 |
| Communications | CMP-009 (4G LTE), CMP-010 (LoRaWAN) | 2 |
| **Total** | | **13** |

---

## What this library does NOT do

- It does not cover all possible components. The library is seeded with 13 components sufficient for the example blueprint. More components will be added as needed.
- It does not guarantee supplier availability. Suppliers and prices change.
- It does not include legacy components (e.g., lead-acid batteries) except as alternatives.
- It does not modify the frozen formula or any prior architecture.

---

## Pre-stated falsifier (EP-4)

**Claim:** The 13 components in this library are sufficient to assemble a functional autonomous agricultural robot.

**Falsifier:** A blueprint that requires a component not in this library — e.g., a manipulator arm, a sprayer, a seeder, a harvester attachment.

**Status:** PENDING. The example blueprint (EXAMPLE_BLUEPRINT_001.md) will test this. If the blueprint requires a component not in the library, the library is incomplete.
