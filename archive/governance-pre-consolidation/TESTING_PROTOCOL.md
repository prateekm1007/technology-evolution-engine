# TESTING_PROTOCOL

**Status:** Phase 17 Deliverable 7.
**Location:** repo root.
**Phase:** 17.

---

## Purpose

Every blueprint must answer five questions (per CEO directive):

```text
Does it work?

Can it be built?

Can it be manufactured?

Can it be maintained?

Can it scale?
```

This document defines the testing protocol for each question. Each
test has a concrete procedure, pass/fail criteria, and a confidence
metric.

---

## Schema

```typescript
interface Test {
    question: "DOES_WORK" | "CAN_BUILD" | "CAN_MANUFACTURE" | "CAN_MAINTAIN" | "CAN_SCALE"
    testName: string
    procedure: string
    passCriteria: string
    confidence: number        // [0, 1]
    result: "PASS" | "FAIL" | "PENDING"
    notes: string
}
```

---

## The five test categories

### Question 1: Does it work?

**Tests whether the robot performs its intended function.**

#### Test 1.1: Navigation accuracy test

| Field | Value |
|---|---|
| question | DOES_WORK |
| testName | Navigation accuracy (RTK-GPS + IMU fusion) |
| procedure | Robot navigates a 100m x 100m rectangular path 10 times. Measure deviation from planned path at 10 points per lap. Record max and RMS deviation. |
| passCriteria | RMS deviation < 5cm; max deviation < 15cm |
| confidence | 0.9 |
| result | PENDING |
| notes | RTK-GPS + IMU fusion expected to achieve 2-3cm RMS in open field |

#### Test 1.2: Autonomy duration test

| Field | Value |
|---|---|
| question | DOES_WORK |
| testName | Autonomy duration (solar + battery) |
| procedure | Robot operates continuously (navigation + sensing) starting at 6:00 AM. Record time until battery < 20%. Test across 3 weather conditions (sunny, cloudy, overcast). |
| passCriteria | ≥ 10 hours autonomy on sunny day; ≥ 6 hours on overcast day |
| confidence | 0.85 |
| result | PENDING |
| notes | Solar charging expected to extend operation beyond battery-only 4-hour limit |

#### Test 1.3: Sensor accuracy test

| Field | Value |
|---|---|
| question | DOES_WORK |
| testName | Soil moisture sensor accuracy |
| procedure | Place 3 soil moisture sensors at 3 depths (10, 20, 30cm) in 5 locations. Compare readings to gravimetric (oven-dry) method. Test across 3 soil types (sandy, loam, clay). |
| passCriteria | Sensor reading within ±3% of gravimetric measurement |
| confidence | 0.8 |
| result | PENDING |
| notes | Capacitive sensors typically achieve ±3%; calibration required per soil type |

#### Test 1.4: Crop detection test

| Field | Value |
|---|---|
| question | DOES_WORK |
| testName | NDVI crop health classification |
| procedure | Robot captures multispectral images of 100 plants with known health status (verified by agronomist). Classify into healthy/stressed/diseased. Compute precision and recall. |
| passCriteria | Precision > 85%; recall > 80% |
| confidence | 0.75 |
| result | PENDING |
| notes | NDVI is a proxy indicator; ground-truth validation required |

### Question 2: Can it be built?

**Tests whether the robot can be assembled from available components.**

#### Test 2.1: Component availability test

| Field | Value |
|---|---|
| question | CAN_BUILD |
| testName | Component sourcing verification |
| procedure | Place orders for all 13 components at production volume (100 units). Verify lead times against SUPPLIER_LIBRARY.md. Identify any components with lead time > 12 weeks. |
| passCriteria | All components available within 12 weeks; no sole-source without alternative |
| confidence | 0.85 |
| result | PENDING |
| notes | Silicon-based components (SPL-005 edge AI, SPL-015 wafers) may have longer lead times during semiconductor cycle |

#### Test 2.2: Assembly feasibility test

| Field | Value |
|---|---|
| question | CAN_BUILD |
| testName | Assembly feasibility (assembly steps + tolerances) |
| procedure | Assemble 5 prototypes following MANUFACTURING_ENGINE assembly steps. Time each step. Identify steps that cannot be completed or require rework. |
| passCriteria | All assembly steps completable; < 5% rework rate; total assembly time < 8 hours |
| confidence | 0.8 |
| result | PENDING |
| notes | Assembly steps from MANUFACTURING_ENGINE.md; tolerances from CAD_SPECIFICATION_SCHEMA.md |

### Question 3: Can it be manufactured?

**Tests whether the robot can be manufactured at scale.**

#### Test 3.1: Yield test

| Field | Value |
|---|---|
| question | CAN_MANUFACTURE |
| testName | Production yield |
| procedure | Manufacture 50 units on production line. Track defects per unit. Compute yield (% of units passing final QC). |
| passCriteria | Yield > 90%; defect rate < 1 per unit |
| confidence | 0.7 |
| result | PENDING |
| notes | Yield depends on tolerance complexity; chassis tolerances are moderate |

#### Test 3.2: Throughput test

| Field | Value |
|---|---|
| question | CAN_MANUFACTURE |
| testName | Production throughput |
| procedure | Measure time per unit on production line. Compute units per day at steady state. |
| passCriteria | ≥ 10 units per day with single shift; ≥ 20 units per day with double shift |
| confidence | 0.75 |
| result | PENDING |
| notes | Throughput depends on assembly station count and balance |

### Question 4: Can it be maintained?

**Tests whether the robot can be serviced in the field.**

#### Test 4.1: MTBF test

| Field | Value |
|---|---|
| question | CAN_MAINTAIN |
| testName | Mean Time Between Failures |
| procedure | Operate 5 robots for 1000 hours each. Record all failures. Compute MTBF. |
| passCriteria | MTBF > 200 hours |
| confidence | 0.7 |
| result | PENDING |
| notes | MTBF depends on component reliability (motors, sensors, battery cycles) |

#### Test 4.2: MTTR test

| Field | Value |
|---|---|
| question | CAN_MAINTAIN |
| testName | Mean Time To Repair |
| procedure | For each failure in MTBF test, measure repair time (diagnosis + parts + labor). Compute MTTR. |
| passCriteria | MTTR < 4 hours (field-repairable within a work day) |
| confidence | 0.75 |
| result | PENDING |
| notes | Requires field-serviceable design (modular components, accessible fasteners) |

#### Test 4.3: Spare parts availability test

| Field | Value |
|---|---|
| question | CAN_MAINTAIN |
| testName | Spare parts supply chain |
| procedure | Order spare parts for all 13 components. Verify availability and lead time for spares. |
| passCriteria | All spares available within 4 weeks; spare kit cost < 10% of unit cost |
| confidence | 0.8 |
| result | PENDING |
| notes | Spares strategy: 2x components for high-failure items (motors, sensors), 1x for low-failure items |

### Question 5: Can it scale?

**Tests whether the robot can scale to market-relevant volume.**

#### Test 5.1: Cost-at-scale test

| Field | Value |
|---|---|
| question | CAN_SCALE |
| testName | Unit cost at production volume |
| procedure | Compute unit cost at 100, 1000, 10000 units using Wright's Law (cost declines ~20% per doubling). Compare to willingness-to-pay by market segment. |
| passCriteria | Unit cost at 1000 units < $15K (medium farm WTP); unit cost at 10000 units < $8K (small farm WTP with leasing) |
| confidence | 0.8 |
| result | PENDING |
| notes | Wright's Law applied to BOM cost; labor and overhead added separately |

#### Test 5.2: Field deployment test

| Field | Value |
|---|---|
| question | CAN_SCALE |
| testName | Multi-farm field deployment |
| procedure | Deploy 20 robots across 5 farms (3 crop types, 2 soil types, 2 climates). Operate for 1 growing season (3-6 months). Collect performance data. |
| passCriteria | ≥ 80% uptime; positive ROI for farm operator; < 2 critical failures per robot per season |
| confidence | 0.7 |
| result | PENDING |
| notes | Field test validates real-world performance, not just lab performance |

---

## Test execution protocol

1. **Pre-production:** Run Tests 1.x, 2.x in lab environment.
2. **Prototype:** Run Tests 1.x, 2.x, 3.x on prototype.
3. **Pre-certification:** Run Tests 4.x (maintenance) on prototype.
4. **Production pilot:** Run Tests 3.x, 5.x on first production batch.
5. **Field deployment:** Run Test 5.2 on production units in real farms.

---

## What this protocol does NOT do

- It does not specify the testing equipment. Equipment depends on the test.
- It does not handle safety testing (e.g., CE safety compliance). Safety is in the certification stage.
- It does not model test cost. Test cost is in the ECONOMIC_ENGINE.
- It does not modify the frozen formula or any prior architecture.

---

## Pre-stated falsifier (EP-4)

**Claim:** The 5 test categories (DOES_WORK, CAN_BUILD, CAN_MANUFACTURE, CAN_MAINTAIN, CAN_SCALE) with the 12 specific tests are sufficient to validate an agricultural robot.

**Falsifier:** A failure mode that is not caught by any of the 12 tests — e.g., a cybersecurity vulnerability, a data privacy issue, or an interoperability problem with existing farm equipment.

**Status:** PENDING. The example blueprint will test this.
