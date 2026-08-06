# CAD_SPECIFICATION_SCHEMA

**Status:** Phase 17 Deliverable 5.
**Location:** repo root.
**Phase:** 17.

---

## Purpose

The CAD Specification Schema defines how geometric parts are
specified in the Blueprint. Per Rule 4 (every output must be
machine-readable), this schema produces geometry that can be
exported to a CAD system (STEP, IGES, or parametric format).

---

## Schema

```typescript
interface GeometrySpecification {
    dimensions: Dimensions
    materials: Material[]
    tolerances: Tolerance[]
    joints: Joint[]
}
```

### Supporting schemas

```typescript
interface Dimensions {
    length_mm: number
    width_mm: number
    height_mm: number
    weight_kg: number
    custom: Record<string, number>  // part-specific dimensions
}

interface Material {
    materialId: string              // from MATERIAL_LIBRARY.md
    usage: string                   // e.g., "structural frame", "housing"
    volume_cm3: number
    mass_kg: number
}

interface Tolerance {
    dimension: string               // e.g., "hole_diameter", "flatness"
    nominal_mm: number
    upperTolerance_mm: number
    lowerTolerance_mm: number
    reason: string                   // why this tolerance is required
}

interface Joint {
    id: string
    type: "WELD" | "BOLT" | "ADHESIVE" | "PRESS_FIT" | "SNAP_FIT"
    parts: string[]                  // part IDs being joined
    specification: string            // e.g., "M6 x 20mm socket head cap screw, torque 8Nm"
    reason: string                    // why this joint type
}
```

---

## Example: Chassis frame for solar irrigation robot

```json
{
  "dimensions": {
    "length_mm": 1800,
    "width_mm": 900,
    "height_mm": 600,
    "weight_kg": 28,
    "custom": {
      "wheelbase_mm": 1200,
      "track_width_mm": 750,
      "ground_clearance_mm": 250,
      "solar_panel_mount_height_mm": 1500
    }
  },
  "materials": [
    {
      "materialId": "MAT-001",
      "usage": "main frame rails (2x)",
      "volume_cm3": 2400,
      "mass_kg": 6.5
    },
    {
      "materialId": "MAT-001",
      "usage": "cross members (4x)",
      "volume_cm3": 1600,
      "mass_kg": 4.3
    },
    {
      "materialId": "MAT-001",
      "usage": "solar panel mount (1x)",
      "volume_cm3": 1800,
      "mass_kg": 4.9
    },
    {
      "materialId": "MAT-007",
      "usage": "motor mounts (4x)",
      "volume_cm3": 800,
      "mass_kg": 6.3
    },
    {
      "materialId": "MAT-007",
      "usage": "wheel hubs (4x)",
      "volume_cm3": 600,
      "mass_kg": 4.7
    },
    {
      "materialId": "MAT-005",
      "usage": "electronics bay housing (1x)",
      "volume_cm3": 2200,
      "mass_kg": 2.4
    }
  ],
  "tolerances": [
    {
      "dimension": "wheel_hub_bore_diameter",
      "nominal_mm": 25.0,
      "upperTolerance_mm": 0.02,
      "lowerTolerance_mm": 0.0,
      "reason": "Press-fit on motor shaft; tolerance required for torque transmission without slipping"
    },
    {
      "dimension": "frame_rail_flatness",
      "nominal_mm": 0.0,
      "upperTolerance_mm": 0.5,
      "lowerTolerance_mm": -0.5,
      "reason": "Mounting surface for solar panel; flatness required to prevent panel stress cracking"
    },
    {
      "dimension": "motor_mount_bolt_pattern",
      "nominal_mm": 100.0,
      "upperTolerance_mm": 0.1,
      "lowerTolerance_mm": -0.1,
      "reason": "Bolt pattern must match motor flange; tolerance required for assembly"
    },
    {
      "dimension": "ground_clearance",
      "nominal_mm": 250.0,
      "upperTolerance_mm": 10.0,
      "lowerTolerance_mm": -10.0,
      "reason": "Agricultural terrain clearance; tolerance is loose to allow for tire variation"
    },
    {
      "dimension": "solar_panel_mount_height",
      "nominal_mm": 1500.0,
      "upperTolerance_mm": 5.0,
      "lowerTolerance_mm": -5.0,
      "reason": "Height above crop canopy; tolerance allows for adjustable mount"
    }
  ],
  "joints": [
    {
      "id": "JT-001",
      "type": "WELD",
      "parts": ["frame_rail_left", "cross_member_front"],
      "specification": "TIG weld, 4mm fillet, continuous, ground smooth",
      "reason": "Permanent structural joint; weld is strongest and lightest for aluminum frame"
    },
    {
      "id": "JT-002",
      "type": "BOLT",
      "parts": ["motor_mount_front_left", "frame_rail_left"],
      "specification": "4x M8 x 25mm socket head cap screws, torque 12Nm, threadlocker blue",
      "reason": "Serviceable joint; motor may need removal for maintenance"
    },
    {
      "id": "JT-003",
      "type": "BOLT",
      "parts": ["solar_panel_mount", "frame_rail_left"],
      "specification": "4x M6 x 20mm button head cap screws, torque 8Nm",
      "reason": "Serviceable joint; solar panel may need removal for transport"
    },
    {
      "id": "JT-004",
      "type": "BOLT",
      "parts": ["wheel_hub_front_left", "frame_rail_left"],
      "specification": "1x M20 x 60mm hex bolt, torque 120Nm, castle nut with cotter pin",
      "reason": "Critical safety joint; wheel retention. Cotter pin prevents loosening"
    },
    {
      "id": "JT-005",
      "type": "ADHESIVE",
      "parts": ["electronics_bay_housing", "lid"],
      "specification": "Silicone gasket adhesive, continuous bead, IP67 seal",
      "reason": "Environmental seal; adhesive provides watertight joint for electronics bay"
    }
  ]
}
```

---

## CAD export protocol

The GeometrySpecification is converted to CAD format as follows:

1. **STEP export:** The geometry (dimensions, materials, tolerances) is converted to STEP (ISO 10303) format, the standard for mechanical CAD interchange.
2. **Parametric model:** The dimensions and tolerances are parameterized in the CAD model, allowing design changes without redrawing.
3. **Bill of materials (BOM):** The materials list is exported as a BOM, cross-referenced with the Component Library and Supplier Library.
4. **Drawing package:** 2D engineering drawings (orthographic projections, section views, detail callouts) are generated from the 3D model.

---

## What this schema does NOT do

- It does not specify surface finish. Surface finish is a manufacturing detail, not a geometric specification.
- It does not specify assembly order. Assembly order is in MANUFACTURING_PIPELINE.md.
- It does not generate the CAD file. It specifies the data that a CAD generator would use.
- It does not modify the frozen formula or any prior architecture.

---

## Pre-stated falsifier (EP-4)

**Claim:** The GeometrySpecification schema (dimensions + materials + tolerances + joints) is sufficient to specify any mechanical part in the agricultural robot.

**Falsifier:** A part that requires specification not in this schema — e.g., surface finish, coating, or kinematic constraints (moving parts).

**Status:** PENDING. The example blueprint will test this.
