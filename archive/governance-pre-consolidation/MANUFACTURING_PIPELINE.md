# MANUFACTURING_PIPELINE

**Status:** Phase 17 Deliverable 6.
**Location:** repo root.
**Phase:** 17.

---

## Purpose

The Manufacturing Pipeline defines the stages through which an
idea becomes a physical product. Per the CEO's directive:

```text
design
   ↓
simulation
   ↓
prototype
   ↓
testing
   ↓
certification
   ↓
production
```

Each stage has inputs, outputs, and a gate. A gate is a review
point where the output must meet criteria before proceeding to the
next stage.

---

## The six stages

### Stage 1: Design

**Input:** IdeaInput (from BLUEPRINT_ENGINE)

**Output:** CAD specification (from CAD_SPECIFICATION_SCHEMA.md), component list (from COMPONENT_LIBRARY.md), BOM (bill of materials)

**Activities:**
- Decompose the idea into subsystems (per DOMAIN_ONTOLOGY_AGRICULTURE.md)
- Select components from COMPONENT_LIBRARY.md
- Design custom parts (chassis, mounts, housings) per CAD_SPECIFICATION_SCHEMA.md
- Generate BOM with quantities, suppliers, costs
- Generate assembly drawings

**Gate:** Design review. Criteria: all components have alternatives, BOM is complete, no single-point-of-failure in supply chain.

### Stage 2: Simulation

**Input:** CAD specification, BOM

**Output:** Simulation results (from SIMULATION_ENGINE.md), failure analysis (from FAILURE_LIBRARY.md)

**Activities:**
- Run CAN_WORK simulation (physics, dependency graph)
- Run CAN_BUILD simulation (manufacturing feasibility)
- Run CAN_FINANCE simulation (economic viability)
- Run CAN_REGULATE simulation (regulatory pathway)
- Run CAN_SCALE simulation (manufacturing throughput, market)
- Identify failure modes (thermal, structural, power, regulatory, manufacturing, economic, coordination)

**Gate:** Simulation review. Criteria: all 5 simulations have answers (true/false with confidence), no failure mode with severity > 0.8 without mitigation.

### Stage 3: Prototype

**Input:** CAD specification, BOM, simulation results

**Output:** Physical prototype, test plan

**Activities:**
- Source components from suppliers (per SUPPLIER_LIBRARY.md)
- Manufacture custom parts (machine shop or contract manufacturer)
- Assemble prototype per assembly steps (from MANUFACTURING_ENGINE.md)
- Load software (ROS2 stack, navigation, control)
- Initial calibration and testing

**Gate:** Prototype review. Criteria: prototype assembled successfully, all subsystems functional, no critical failures in initial testing.

### Stage 4: Testing

**Input:** Physical prototype, test plan (from TESTING_PROTOCOL.md)

**Output:** Test report, iteration backlog

**Activities:**
- Environmental testing (IP67 sealing, temperature, vibration, UV)
- Functional testing (navigation accuracy, autonomy duration, sensor accuracy)
- Reliability testing (MTBF, MTTR)
- Field testing (on actual farms, multi-crop, multi-terrain)
- Iterate on failures (per FAILURE_LIBRARY.md)

**Gate:** Testing review. Criteria: all test categories pass at > 90% reliability, no safety-critical failures, iteration backlog addresses all critical issues.

### Stage 5: Certification

**Input:** Test report, design documentation

**Output:** Certification documents (CE mark, FCC ID, EPA registration, etc.)

**Activities:**
- Submit to regulatory bodies (per REGULATORY_ENGINE.md)
- Conduct any required third-party testing
- Address regulatory feedback
- Obtain certifications

**Gate:** Certification review. Criteria: all required certifications obtained for target jurisdictions, no outstanding regulatory blockers.

### Stage 6: Production

**Input:** Certified design, production tooling

**Output:** Production units

**Activities:**
- Set up production line (per MANUFACTURING_ENGINE.md)
- Source components at production volume
- Train production staff
- Quality control (yield, defect tracking)
- Scale to target volume

**Gate:** Production readiness review. Criteria: yield > 90%, cost per unit meets target, supplier capacity confirmed, logistics in place.

---

## Pipeline diagram

```
┌──────────┐
│ Design   │ ← IdeaInput (BLUEPRINT_ENGINE)
└────┬─────┘
     │ gate: design review
     ▼
┌──────────┐
│Simulation│ ← CAD spec + BOM
└────┬─────┘
     │ gate: simulation review (5 sims, failure modes)
     ▼
┌──────────┐
│Prototype │ ← Components + manufacturing
└────┬─────┘
     │ gate: prototype review (assembled, functional)
     ▼
┌──────────┐
│ Testing  │ ← Test plan (TESTING_PROTOCOL)
└────┬─────┘
     │ gate: testing review (>90% reliability)
     ▼
┌──────────┐
│Certify   │ ← Regulatory (REGULATORY_ENGINE)
└────┬─────┘
     │ gate: certification review (all certs obtained)
     ▼
┌──────────┐
│Production│ ← Manufacturing (MANUFACTURING_ENGINE)
└──────────┘
     gate: production readiness (yield >90%, cost target met)
```

---

## Timeline estimates (per stage)

| Stage | Duration | Notes |
|---|---|---|
| Design | 2-4 months | Depends on complexity; reuses COMPONENT_LIBRARY |
| Simulation | 2-4 weeks | Computational; runs on existing hardware |
| Prototype | 1-2 months | Component lead time + assembly + calibration |
| Testing | 3-6 months | Field testing across seasons; multiple iterations |
| Certification | 3-12 months | Jurisdiction-dependent; parallel with testing |
| Production setup | 3-6 months | Tooling, supplier scaling, staff training |
| **Total** | **14-32 months** | Parallel tracks reduce total to ~18-24 months |

---

## What this pipeline does NOT do

- It does not guarantee success at each stage. Gates may fail, requiring iteration.
- It does not handle parallel tracks (e.g., certification can run in parallel with testing). The pipeline is sequential for clarity; actual execution may overlap stages.
- It does not specify the cost of each stage. Cost is in the ECONOMIC_ENGINE.md.
- It does not modify the frozen formula or any prior architecture.

---

## Pre-stated falsifier (EP-4)

**Claim:** The 6 stages (design → simulation → prototype → testing → certification → production) cover all steps from idea to physical product.

**Falsifier:** A step that is not in the pipeline — e.g., "market research" (before design), "customer feedback" (during testing), "end-of-life recycling" (after production).

**Status:** PENDING. The example blueprint will test this.
