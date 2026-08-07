#!/usr/bin/env python3
"""
prototype_compiler.py — Stage VI: Turn a Configuration into something buildable.

Takes a candidate Configuration and produces a Prototype — a complete
build package containing:

  - Materials list (with role, supplier placeholder, cost)
  - Parameters list (with values, tolerances, units)
  - Assembly steps (ordered, with step type and instruction)
  - Predicted behavior (from the forward model)
  - Failure modes (with likelihood and mitigation)
  - BOM (bill of materials)
  - Manufacturing constraints (CHECKED against the configuration)

Manufacturing constraints are real, not decorative. The compiler checks:

  - Minimum feature size (thickness >= min_feature_size)
  - Maximum layer count (n_layers <= max_layers)
  - Maximum operating temperature (T_hot <= material max_temp)
  - Allowed materials (each material must be in the allowed list)
  - Cost ceiling (sum of BOM <= cost ceiling, if specified)

If any constraint is violated, the violation is recorded and the
Prototype's `manufacturing_pass` flag is set to False. The compiler
does NOT silently "fix" the configuration — it reports the violation
honestly (Constitution: Honest-Boundary Rule).

Usage:
    from scripts.prototype_compiler import PrototypeCompiler
    prototype = PrototypeCompiler().compile(configuration)
    if prototype.manufacturing_pass:
        # ... build it
"""
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.artifact_generator import Configuration, Component, MATERIAL_PARAMS
from scripts.forward_model import ForwardModel, Prediction


# ---------------------------------------------------------------------------
# Manufacturing constraints (defaults — conservative engineering limits).
# ---------------------------------------------------------------------------
DEFAULT_CONSTRAINTS: Dict[str, Any] = {
    "min_feature_size_m": 1.0e-5,        # 10 µm
    "max_layers": 10,
    "max_operating_temp_K": 800.0,
    "allowed_materials": list(MATERIAL_PARAMS.keys()),
    "cost_ceiling_usd": 1000.0,
    "max_component_count": 8,
}

# Failure-mode templates per domain.
# Each is {mode, likelihood (0-1), mitigation, evidence_rank}.
FAILURE_MODES: Dict[str, List[Dict[str, Any]]] = {
    "thermoelectric": [
        {"mode": "contact_resistance_at_electrode",
         "likelihood": 0.6,
         "mitigation": "Use silver paste + diffusion barrier (Ti/W) at electrode interface; apply 5 MPa contact pressure.",
         "evidence_rank": "D"},
        {"mode": "thermal_cycling_fatigue",
         "likelihood": 0.4,
         "mitigation": "Match CTE between leg and electrode; use compliant interlayer.",
         "evidence_rank": "D"},
        {"mode": "sublimation_of_tellurium_at_high_T",
         "likelihood": 0.5 if False else 0.3,
         "mitigation": "Cap with SiN_x passivation; operate below 600 K.",
         "evidence_rank": "D"},
        {"mode": "oxidation_of_leg",
         "likelihood": 0.2,
         "mitigation": "Encapsulate in inert atmosphere (Ar) or apply Al2O3 coating.",
         "evidence_rank": "D"},
    ],
    "thermal": [
        {"mode": "dust_deposition_on_emissive_surface",
         "likelihood": 0.7,
         "mitigation": "Use hydrophobic PE protective film; clean monthly.",
         "evidence_rank": "G"},
        {"mode": "condensation_on_cold_surface",
         "likelihood": 0.5,
         "mitigation": "Add convection shield or PDMS anti-condensation coating.",
         "evidence_rank": "G"},
        {"mode": "emissivity_degradation",
         "likelihood": 0.3,
         "mitigation": "Use UV-stable pigment (TiO2); refresh coating every 5 years.",
         "evidence_rank": "F"},
    ],
    "supercapacitor": [
        {"mode": "electrolyte_dryout",
         "likelihood": 0.5,
         "mitigation": "Hermetic packaging; use ionic liquid electrolyte.",
         "evidence_rank": "D"},
        {"mode": "electrode_delamination",
         "likelihood": 0.3,
         "mitigation": "Use PVDF binder at 8 wt%; calender at 200 MPa.",
         "evidence_rank": "D"},
    ],
    "default": [
        {"mode": "manufacturing_tolerance_exceeded",
         "likelihood": 0.3,
         "mitigation": "Use statistical process control; sample 1 in 10 parts.",
         "evidence_rank": "F"},
    ],
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class MaterialSpec:
    """One material entry in the BOM."""
    material: str
    role: str
    quantity_kg: float
    cost_per_kg: float
    cost_usd: float
    supplier: str = "TBD"
    notes: str = ""


@dataclass
class ParameterSpec:
    """One parameter with value, tolerance, units."""
    name: str
    value: float
    tolerance: float       # ± absolute
    units: str
    description: str = ""


@dataclass
class AssemblyStep:
    """One assembly step."""
    step: int
    operation: str         # "deposit", "press", "sinter", "wire", "encapsulate", etc.
    target: str            # which material/component
    instruction: str
    duration_min: float = 0.0
    temperature_K: Optional[float] = None
    pressure_Pa: Optional[float] = None


@dataclass
class FailureMode:
    """A potential failure mode with mitigation."""
    mode: str
    likelihood: float
    mitigation: str
    evidence_rank: str


@dataclass
class ConstraintViolation:
    """A manufacturing constraint violation."""
    constraint: str
    expected: Any
    actual: Any
    severity: str          # "error" or "warning"
    message: str


@dataclass
class Prototype:
    """The buildable output of Stage VI."""
    config_id: str
    config_hash: str
    domain: str
    materials: List[MaterialSpec] = field(default_factory=list)
    parameters: List[ParameterSpec] = field(default_factory=list)
    assembly_steps: List[AssemblyStep] = field(default_factory=list)
    predicted_behavior: Dict[str, Any] = field(default_factory=dict)
    failure_modes: List[FailureMode] = field(default_factory=list)
    bom: List[MaterialSpec] = field(default_factory=list)
    bom_total_cost_usd: float = 0.0
    manufacturing_constraints: Dict[str, Any] = field(default_factory=dict)
    constraint_violations: List[ConstraintViolation] = field(default_factory=list)
    manufacturing_pass: bool = True
    timestamp: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "config_id": self.config_id,
            "config_hash": self.config_hash,
            "domain": self.domain,
            "materials": [asdict(m) for m in self.materials],
            "parameters": [asdict(p) for p in self.parameters],
            "assembly_steps": [asdict(s) for s in self.assembly_steps],
            "predicted_behavior": self.predicted_behavior,
            "failure_modes": [asdict(f) for f in self.failure_modes],
            "bom": [asdict(m) for m in self.bom],
            "bom_total_cost_usd": self.bom_total_cost_usd,
            "manufacturing_constraints": self.manufacturing_constraints,
            "constraint_violations": [asdict(v) for v in self.constraint_violations],
            "manufacturing_pass": self.manufacturing_pass,
            "timestamp": self.timestamp,
            "provenance": self.provenance,
        }


class PrototypeCompiler:
    """Stage VI: compile a Configuration into a buildable Prototype."""

    def __init__(self,
                 constraints: Optional[Dict[str, Any]] = None,
                 forward_model: Optional[ForwardModel] = None):
        self.constraints = dict(DEFAULT_CONSTRAINTS)
        if constraints:
            self.constraints.update(constraints)
        self.forward_model = forward_model or ForwardModel()

    # ----- public API ---------------------------------------------------
    def compile(self, config: Configuration,
                prediction: Optional[Prediction] = None) -> Prototype:
        """Compile a Configuration into a buildable Prototype.

        Args:
            config: the candidate Configuration
            prediction: optional pre-computed Prediction (else computed here)

        Returns:
            a Prototype with materials, parameters, assembly steps,
            predicted behavior, failure modes, BOM, and constraint
            violations listed.
        """
        if prediction is None:
            prediction = self.forward_model.predict(config)

        materials = self._build_materials(config)
        parameters = self._build_parameters(config, prediction)
        assembly_steps = self._build_assembly_steps(config)
        failure_modes = self._build_failure_modes(config)
        bom = list(materials)
        bom_total = sum(m.cost_usd for m in bom)
        violations = self._check_constraints(config, materials, bom_total)

        return Prototype(
            config_id=config.config_id,
            config_hash=config.config_hash,
            domain=config.domain,
            materials=materials,
            parameters=parameters,
            assembly_steps=assembly_steps,
            predicted_behavior=prediction.to_dict(),
            failure_modes=failure_modes,
            bom=bom,
            bom_total_cost_usd=round(bom_total, 2),
            manufacturing_constraints=dict(self.constraints),
            constraint_violations=violations,
            manufacturing_pass=(len(violations) == 0),
            timestamp=datetime.now(timezone.utc).isoformat(),
            provenance={
                "compiler": "PrototypeCompiler",
                "stage": "VI",
                "constraint_check": "explicit",
                "forward_model": "ForwardModel",
            },
        )

    # ----- materials & BOM ---------------------------------------------
    def _build_materials(self, config: Configuration) -> List[MaterialSpec]:
        """Build the materials list and BOM."""
        materials: List[MaterialSpec] = []
        # Approximate the mass of each component from density × volume.
        # Volume = area × thickness (from global params, divided among components).
        A = config.parameters.get("area_m2", 1.0e-4)
        L = config.parameters.get("thickness_m", 1.0e-3)
        n = max(1, len(config.components))
        per_comp_thickness = L / n
        for c in config.components:
            params = MATERIAL_PARAMS.get(c.material, {})
            density = params.get("density", c.parameters.get("density", 1000.0))
            cost_per_kg = params.get("cost_per_kg", c.parameters.get("cost_per_kg", 0.0))
            mass = density * A * per_comp_thickness
            cost = mass * cost_per_kg
            materials.append(MaterialSpec(
                material=c.material,
                role=c.role,
                quantity_kg=round(mass, 6),
                cost_per_kg=round(cost_per_kg, 2),
                cost_usd=round(cost, 2),
                supplier="TBD",
                notes=f"volume={A*per_comp_thickness:.2e} m^3",
            ))
        return materials

    # ----- parameters --------------------------------------------------
    def _build_parameters(self, config: Configuration,
                          prediction: Prediction) -> List[ParameterSpec]:
        """Build the parameter list with tolerances."""
        params: List[ParameterSpec] = []
        # Component-level parameters
        for i, c in enumerate(config.components):
            for pname, pval in c.parameters.items():
                tol = self._tolerance_for(pname, pval)
                params.append(ParameterSpec(
                    name=f"component[{i}].{c.material}.{pname}",
                    value=round(pval, 8) if isinstance(pval, float) else pval,
                    tolerance=tol,
                    units=self._units_for(pname),
                    description=f"{pname} of {c.material} ({c.role})",
                ))
        # Global parameters
        for pname, pval in config.parameters.items():
            tol = self._tolerance_for(pname, pval)
            params.append(ParameterSpec(
                name=f"global.{pname}",
                value=round(pval, 8) if isinstance(pval, float) else pval,
                tolerance=tol,
                units=self._units_for(pname),
                description=f"global {pname}",
            ))
        return params

    def _tolerance_for(self, name: str, value: float) -> float:
        """Return the absolute tolerance for a parameter."""
        rel = {
            "thickness_m": 0.05,
            "area_m2": 0.05,
            "T_hot_K": 0.02,
            "T_cold_K": 0.02,
            "seebeck_coefficient": 0.10,
            "electrical_conductivity": 0.20,
            "thermal_conductivity": 0.15,
            "porosity": 0.20,
            "n_layers": 0.0,           # exact
            "n_segments": 0.0,
            "modulation_freq": 0.10,
            "substitution_fraction": 0.05,
        }.get(name, 0.10)
        return round(abs(value) * rel, 8) if isinstance(value, (int, float)) else 0.0

    def _units_for(self, name: str) -> str:
        units_map = {
            "thickness_m": "m", "area_m2": "m^2",
            "T_hot_K": "K", "T_cold_K": "K",
            "seebeck_coefficient": "V/K",
            "electrical_conductivity": "S/m",
            "thermal_conductivity": "W/(m·K)",
            "density": "kg/m^3", "cost_per_kg": "USD/kg",
            "max_temp": "K",
            "porosity": "dimensionless",
            "n_layers": "count",
            "n_segments": "count",
            "modulation_freq": "Hz",
            "substitution_fraction": "dimensionless",
        }
        return units_map.get(name, "dimensionless")

    # ----- assembly steps ----------------------------------------------
    def _build_assembly_steps(self, config: Configuration) -> List[AssemblyStep]:
        """Build ordered assembly steps."""
        steps: List[AssemblyStep] = []
        step_n = 1

        # Step 1: substrate preparation
        steps.append(AssemblyStep(
            step=step_n, operation="prepare",
            target="substrate",
            instruction="Clean substrate with acetone + IPA; dry N2.",
            duration_min=10.0,
        ))
        step_n += 1

        # Step 2-N: deposit/synthesize each component
        for c in config.components:
            op = self._deposit_op_for(c.material)
            T = MATERIAL_PARAMS.get(c.material, {}).get("max_temp", 500.0)
            steps.append(AssemblyStep(
                step=step_n,
                operation=op,
                target=c.material,
                instruction=(
                    f"{op} {c.material} as {c.role} "
                    f"(target thickness {config.parameters.get('thickness_m', 1e-3)/max(1,len(config.components)):.2e} m)."
                ),
                duration_min=30.0 if op == "sinter" else 15.0,
                temperature_K=round(T * 0.6, 1),  # process at ~60% of max
                pressure_Pa=5.0e6 if op == "press" else None,
            ))
            step_n += 1

        # Layered structures: add interlayer steps
        if config.structure.startswith("layered_"):
            n_layers = int(config.structure.split("_")[1])
            steps.append(AssemblyStep(
                step=step_n, operation="stack",
                target=f"{n_layers}_layers",
                instruction=(f"Stack {n_layers} layers with adhesive interleaf; "
                             f"apply 2 MPa uniaxial pressure; cure 60 min @ 80°C."),
                duration_min=60.0,
                temperature_K=353.15,
                pressure_Pa=2.0e6,
            ))
            step_n += 1

        # Segmented structures: add dicing step
        if config.structure.startswith("segmented_"):
            n_seg = int(config.structure.split("_")[1])
            steps.append(AssemblyStep(
                step=step_n, operation="dice",
                target=f"{n_seg}_segments",
                instruction=(f"Dice into {n_seg} segments with diamond saw; "
                             f"mount on common substrate."),
                duration_min=20.0,
            ))
            step_n += 1

        # Wire-bonding for electrodes
        if any(c.role in ("electrode", "active", "active+lead_telluride")
               for c in config.components):
            steps.append(AssemblyStep(
                step=step_n, operation="wire",
                target="electrodes",
                instruction="Wire-bond 25 µm Au wire to electrodes; "
                            "verify continuity < 0.1 Ω.",
                duration_min=15.0,
            ))
            step_n += 1

        # Encapsulation
        steps.append(AssemblyStep(
            step=step_n, operation="encapsulate",
            target="assembly",
            instruction="Encapsulate in epoxy or glass; hermetic seal test.",
            duration_min=45.0,
        ))
        return steps

    def _deposit_op_for(self, material: str) -> str:
        """Pick a deposition operation based on material class."""
        if material in ("bismuth_telluride", "lead_telluride"):
            return "sinter"
        if material in ("copper", "silicon"):
            return "sputter"
        if material in ("graphene",):
            return "cvd"
        if material in ("aerogel",):
            return "sol-gel"
        if material in ("polymer",):
            return "spincoat"
        return "deposit"

    # ----- failure modes -----------------------------------------------
    def _build_failure_modes(self, config: Configuration) -> List[FailureMode]:
        """Build the failure-mode list for the configuration's domain."""
        domain = (config.domain or "default").lower()
        templates = FAILURE_MODES.get(domain, FAILURE_MODES["default"])
        return [FailureMode(
            mode=t["mode"],
            likelihood=t["likelihood"],
            mitigation=t["mitigation"],
            evidence_rank=t["evidence_rank"],
        ) for t in templates]

    # ----- constraint checks -------------------------------------------
    def _check_constraints(self, config: Configuration,
                            materials: List[MaterialSpec],
                            bom_total: float) -> List[ConstraintViolation]:
        """Check manufacturing constraints. Returns violations (may be empty)."""
        violations: List[ConstraintViolation] = []

        # 1. Minimum feature size (thickness)
        thickness = config.parameters.get("thickness_m", 1.0e-3)
        min_fs = self.constraints["min_feature_size_m"]
        if thickness < min_fs:
            violations.append(ConstraintViolation(
                constraint="min_feature_size_m",
                expected=f">= {min_fs} m",
                actual=f"{thickness} m",
                severity="error",
                message=(f"Thickness {thickness:.2e} m is below minimum "
                         f"feature size {min_fs:.2e} m"),
            ))

        # 2. Maximum layer count
        if config.structure.startswith("layered_"):
            try:
                n_layers = int(config.structure.split("_")[1])
            except (ValueError, IndexError):
                n_layers = 0
            max_layers = self.constraints["max_layers"]
            if n_layers > max_layers:
                violations.append(ConstraintViolation(
                    constraint="max_layers",
                    expected=f"<= {max_layers}",
                    actual=f"{n_layers}",
                    severity="error",
                    message=(f"Layer count {n_layers} exceeds max {max_layers}"),
                ))

        # 3. Maximum operating temperature
        T_hot = config.parameters.get("T_hot_K", 300.0)
        max_T = self.constraints["max_operating_temp_K"]
        # Also check material-specific max_temp
        for c in config.components:
            mat_max_T = MATERIAL_PARAMS.get(c.material, {}).get(
                "max_temp", c.parameters.get("max_temp", max_T))
            if T_hot > mat_max_T:
                violations.append(ConstraintViolation(
                    constraint="material_max_temp",
                    expected=f"T_hot <= {mat_max_T} K (material {c.material})",
                    actual=f"{T_hot} K",
                    severity="error",
                    message=(f"T_hot {T_hot} K exceeds material {c.material} "
                             f"max_temp {mat_max_T} K"),
                ))
        if T_hot > max_T:
            violations.append(ConstraintViolation(
                constraint="max_operating_temp_K",
                expected=f"<= {max_T} K",
                actual=f"{T_hot} K",
                severity="error",
                message=f"T_hot {T_hot} K exceeds max operating temp {max_T} K",
            ))

        # 4. Allowed materials
        allowed = set(self.constraints["allowed_materials"])
        for c in config.components:
            # The material might be a composite (e.g., "active+lead_telluride"
            # after substitute). Check the base name.
            mat_name = c.material.split("+")[0]
            if mat_name not in allowed:
                violations.append(ConstraintViolation(
                    constraint="allowed_materials",
                    expected=f"one of {sorted(allowed)}",
                    actual=c.material,
                    severity="error",
                    message=f"Material '{c.material}' not in allowed list",
                ))

        # 5. Cost ceiling
        cost_ceiling = self.constraints.get("cost_ceiling_usd")
        if cost_ceiling is not None and bom_total > cost_ceiling:
            violations.append(ConstraintViolation(
                constraint="cost_ceiling_usd",
                expected=f"<= {cost_ceiling} USD",
                actual=f"{bom_total:.2f} USD",
                severity="warning",
                message=(f"BOM total ${bom_total:.2f} exceeds cost ceiling "
                         f"${cost_ceiling}"),
            ))

        # 6. Max component count
        max_components = self.constraints["max_component_count"]
        if len(config.components) > max_components:
            violations.append(ConstraintViolation(
                constraint="max_component_count",
                expected=f"<= {max_components}",
                actual=f"{len(config.components)}",
                severity="error",
                message=(f"Component count {len(config.components)} exceeds "
                         f"max {max_components}"),
            ))

        return violations


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
def main():
    """Demo: compile a generated configuration into a Prototype."""
    print("=" * 60)
    print("PROTOTYPE COMPILER (Stage VI)")
    print("=" * 60)
    print()

    from scripts.artifact_generator import ArtifactGenerator
    from scripts.specification import SpecificationEngine
    from scripts.capability_graph import CapabilityGraph

    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([
        ("bismuth telluride", "generates", "voltage"),
        ("bismuth telluride", "conducts", "electricity"),
    ])
    configs = ArtifactGenerator(seed=42).generate(spec, cg, n=3)

    compiler = PrototypeCompiler()
    for c in configs:
        proto = compiler.compile(c)
        print(f"\n  {proto.config_id}  hash={proto.config_hash}")
        print(f"    manufacturing_pass: {proto.manufacturing_pass}")
        print(f"    BOM: ${proto.bom_total_cost_usd:.2f}")
        for m in proto.bom:
            print(f"      - {m.material} ({m.role}): "
                  f"{m.quantity_kg*1000:.3f} g @ ${m.cost_per_kg}/kg = ${m.cost_usd:.4f}")
        print(f"    assembly steps: {len(proto.assembly_steps)}")
        for s in proto.assembly_steps[:3]:
            print(f"      [{s.step}] {s.operation} {s.target}: {s.instruction[:60]}...")
        if len(proto.assembly_steps) > 3:
            print(f"      ... +{len(proto.assembly_steps)-3} more steps")
        print(f"    failure modes: {len(proto.failure_modes)}")
        for fm in proto.failure_modes[:2]:
            print(f"      - {fm.mode} (p={fm.likelihood})")
        print(f"    constraint violations: {len(proto.constraint_violations)}")
        for v in proto.constraint_violations:
            print(f"      [{v.severity}] {v.constraint}: {v.message}")
        print(f"    predicted behavior: {list(proto.predicted_behavior.get('predicted_properties', {}).keys())}")

    # Force a constraint violation
    print()
    print("  Constraint violation demo:")
    from scripts.artifact_generator import Component
    bad = Configuration(
        config_id="BAD", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="layered_20",  # exceeds max_layers
        parameters={"thickness_m": 1e-7,  # below min feature size
                    "area_m2": 1e-4, "T_hot_K": 900.0,  # above max operating temp
                    "T_cold_K": 300.0, "n_layers": 20.0},
        design_operator_chain=["init", "layer"],
    )
    bad.config_hash = bad.compute_hash()
    bad_proto = compiler.compile(bad)
    print(f"    manufacturing_pass: {bad_proto.manufacturing_pass}")
    print(f"    violations: {len(bad_proto.constraint_violations)}")
    for v in bad_proto.constraint_violations:
        print(f"      [{v.severity}] {v.constraint}: {v.message}")


if __name__ == "__main__":
    main()
