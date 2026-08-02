# DOMAIN_ONTOLOGY_AGRICULTURE

**Status:** Phase 17 Deliverable 1.
**Location:** repo root.
**Phase:** 17.

> Build depth before breadth.
> — CEO directive, Phase 17

---

## Purpose

This document defines the domain ontology for autonomous agricultural
systems. Per the CEO's directive, agriculture is the vertical-slice
domain because it contains almost every component of the
architecture (sensors, motors, batteries, software, manufacturing,
supply chains, regulations, economics, distribution) in a single
domain.

This ontology is the foundation for the component library, the
example blueprint, and all other Phase 17 deliverables.

---

## Schema

```typescript
interface AgriculturalSystem {
    energySystem: EnergySystem
    controlSystem: ControlSystem
    navigationSystem: NavigationSystem
    communicationsSystem: CommunicationsSystem
    sensorSystem: SensorSystem
}
```

### Subsystem schemas

```typescript
interface EnergySystem {
    primarySource: string       // e.g., "solar", "diesel", "grid"
    storageType: string         // e.g., "li-ion", "lead-acid"
    capacitykWh: number
    peakPowerkW: number
    autonomyHours: number
}

interface ControlSystem {
    processorType: string       // e.g., "ARM Cortex-A72", "ESP32"
    memoryGB: number
    operatingSystem: string    // e.g., "ROS2 Humble", "FreeRTOS"
    aiAccelerator: string | null  // e.g., "NVIDIA Jetson", null if none
}

interface NavigationSystem {
    positioningSystem: string   // e.g., "RTK-GPS", "RTK-GPS + dead reckoning"
    accuracyMeters: number
    obstacleDetection: string  // e.g., "LiDAR", "stereo camera", "LiDAR + camera"
    pathPlanningAlgorithm: string  // e.g., "A*", "RRT", "model predictive control"
}

interface CommunicationsSystem {
    primaryLink: string        // e.g., "4G LTE", "LoRaWAN", "5G"
    backupLink: string         // e.g., "satellite", "mesh"
    rangeKm: number
    bandwidthMbps: number
}

interface SensorSystem {
    environmentalSensors: string[]   // e.g., ["temperature", "humidity", "soil_moisture"]
    cropSensors: string[]            // e.g., ["NDVI", "multispectral"]
    systemSensors: string[]         // e.g., ["battery_voltage", "motor_temperature"]
}
```

---

## The five subsystems

### 1. EnergySystem

The energy system powers the agricultural robot. In agricultural
contexts, solar power is the primary renewable source (farms have
open sky), with Li-ion battery storage for nighttime operation.

**Key design decisions:**
- Primary source: solar (monocrystalline panels, 18-22% efficiency)
- Storage: Li-ion (LFP chemistry for thermal safety in field conditions)
- Capacity: sized for 8-12 hours of autonomous operation
- Peak power: sized for motor loads (typically 0.5-2 kW for small robots)

**Why this matters:** The energy system is the first bottleneck
in agricultural robotics. A robot that cannot operate through a
full day-night cycle requires frequent returns to base, reducing
utilization below the economic threshold.

### 2. ControlSystem

The control system processes sensor data, makes decisions, and
commands actuators. For agricultural robots, the control system
must handle:
- Real-time navigation (10-100 Hz update rate)
- Crop detection and classification (inference at 5-30 fps)
- Implement control (precision agriculture: seed, spray, harvest)
- Fleet coordination (multi-robot systems)

**Key design decisions:**
- Processor: ARM Cortex-A72 or equivalent (sufficient for ROS2 + edge AI)
- Memory: 4-8 GB (sufficient for mapping + inference)
- OS: ROS2 Humble (industry standard for robotics)
- AI accelerator: NVIDIA Jetson Orin Nano (for vision-based navigation)

### 3. NavigationSystem

The navigation system determines the robot's position and plans
paths through the agricultural environment. Key challenges:
- RTK-GPS provides centimeter accuracy in open fields
- Obstacle detection (people, animals, equipment, crop rows)
- Path planning in semi-structured environments (rows, headlands)

**Key design decisions:**
- Positioning: RTK-GPS (centimeter accuracy, requires base station or NTRIP service)
- Obstacle detection: LiDAR (robust in dust and varying light) + stereo camera (for crop identification)
- Path planning: A* for known routes, MPC for real-time obstacle avoidance

### 4. CommunicationsSystem

The communications system enables remote monitoring, fleet
coordination, and data upload. Agricultural environments have
variable cellular coverage.

**Key design decisions:**
- Primary: 4G LTE (adequate in most agricultural areas, sufficient for telemetry)
- Backup: LoRaWAN (long range, low bandwidth — for basic status when cellular is absent)
- Range: 5-15 km (LoRaWAN), 35 km (LTE cell)
- Bandwidth: 10-50 Mbps (LTE), 0.1-50 kbps (LoRaWAN)

### 5. SensorSystem

The sensor system collects data about the environment, crops, and
the robot's own health. Precision agriculture relies on this data
for decision-making.

**Key design decisions:**
- Environmental: temperature, humidity, soil moisture (for irrigation decisions)
- Crop: NDVI (normalized difference vegetation index, for crop health)
- System: battery voltage, motor temperature, GPS status (for diagnostics)

---

## Domain-specific considerations

### Environmental robustness

Agricultural robots operate outdoors in all weather conditions:
- IP67 sealing minimum (dust and water)
- Operating temperature: -10°C to +50°C
- UV resistance for plastic components
- Vibration resistance for off-road operation

### Regulatory environment

Agricultural robots face a fragmented regulatory landscape:
- US: state-by-state autonomous vehicle regulations (varies widely)
- EU: CE marking + Machinery Directive 2006/42/EC
- India: no specific autonomous agricultural vehicle regulation (permissive)
- Pesticide application: EPA certification (US), equivalent in other jurisdictions

### Economic constraints

- Small farms (common in India, parts of Africa): willingness-to-pay $2,000-5,000
- Medium farms (US Midwest): willingness-to-pay $15,000-50,000
- Large farms (corporate): willingness-to-pay $50,000-200,000

The economic model must account for this stratification. A robot
that works for large farms may not be viable for small farms
without a leasing or cooperative-ownership model.

---

## What this ontology does NOT do

- It does not specify a particular robot design. The ontology defines the SUBSYSTEMS; the specific design is in EXAMPLE_BLUEPRINT_001.md.
- It does not cover livestock management (different subsystem requirements).
- It does not cover indoor farming (different energy, communications, and regulatory context).
- It does not modify the frozen formula or any Phase 15/16 architecture.

---

## Pre-stated falsifier (EP-4)

**Claim:** The 5 subsystems (Energy, Control, Navigation, Communications, Sensor) cover all functional requirements of an autonomous agricultural system.

**Falsifier:** An agricultural robot that requires a subsystem not in this ontology — e.g., a manipulation subsystem (for picking fruit), a processing subsystem (for on-board crop processing), or a human-robot interaction subsystem (for collaboration with farm workers).

**Status:** PENDING. The example blueprint (EXAMPLE_BLUEPRINT_001.md) will test this claim. If the blueprint requires a subsystem not in the ontology, the ontology is incomplete.
