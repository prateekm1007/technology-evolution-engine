#!/usr/bin/env python3
"""
artifact_generator.py — Stage II: Generate candidate artifacts.

Design operators (12): combine, replace, invert, amplify, attenuate,
split, merge, layer, stabilize, modulate, substitute, parameterize.

The generator takes a Specification + CapabilityGraph and produces
Configuration objects (structured data, not prose). Generation is
deterministic under a seed.

The Configuration dataclass and the design operators are the canonical
artifacts that flow through Stages III–VII of the invention loop:

    Specification → ArtifactGenerator.generate() → Configuration
                                                      ↓
                                           ForwardModel.predict()
                                                      ↓
                                           NoveltyEngine.check()
                                                      ↓
                                           PrototypeCompiler.compile()
                                                      ↓
                                           MeasurementEngine.run()

Usage:
    from scripts.artifact_generator import ArtifactGenerator
    from scripts.specification import SpecificationEngine
    from scripts.capability_graph import CapabilityGraph

    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([("bismuth_telluride", "generates", "voltage")])
    gen = ArtifactGenerator(seed=42)
    configs = gen.generate(spec, cg, n=5)

See docs/ARTIFACT_SCHEMA.md for the full schema.
"""
import sys
import json
import hashlib
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ---------------------------------------------------------------------------
# Material parameter tables.
#
# Values are typical literature values (evidence rank D in the Constitution's
# evidence hierarchy). They are deliberately conservative — the generator
# may amplify, attenuate, substitute, or otherwise modify them via design
# operators, and the forward model and measurement engine must predict and
# measure the modified configuration, not the catalog value.
# ---------------------------------------------------------------------------
MATERIAL_PARAMS: Dict[str, Dict[str, float]] = {
    "bismuth_telluride": {
        "seebeck_coefficient": 200e-6,      # V/K  (~200 µV/K at 300K)
        "electrical_conductivity": 1.0e5,   # S/m
        "thermal_conductivity": 1.5,        # W/(m·K)
        "temperature": 300.0,               # K (peak operating temperature)
        "density": 7700.0,                  # kg/m^3
        "cost_per_kg": 200.0,               # USD/kg
        "max_temp": 600.0,                  # K (decomposition)
    },
    "lead_telluride": {
        "seebeck_coefficient": 250e-6,
        "electrical_conductivity": 7.0e4,
        "thermal_conductivity": 2.5,
        "temperature": 773.0,
        "density": 8200.0,
        "cost_per_kg": 100.0,
        "max_temp": 800.0,
    },
    "copper": {
        "electrical_conductivity": 5.96e7,
        "thermal_conductivity": 401.0,
        "seebeck_coefficient": 1.94e-6,
        "temperature": 300.0,
        "density": 8960.0,
        "cost_per_kg": 9.0,
        "max_temp": 1358.0,
    },
    "tin_selenide": {
        "seebeck_coefficient": 510e-6,
        "electrical_conductivity": 2.5e3,
        "thermal_conductivity": 0.23,
        "temperature": 923.0,
        "density": 6179.0,
        "cost_per_kg": 50.0,
        "max_temp": 923.0,
    },
    "graphene": {
        "electrical_conductivity": 1.0e8,
        "thermal_conductivity": 5000.0,
        "seebeck_coefficient": 30e-6,
        "density": 2200.0,
        "cost_per_kg": 1000.0,
        "max_temp": 4000.0,
    },
    "polymer": {
        "electrical_conductivity": 1e-15,
        "thermal_conductivity": 0.2,
        "seebeck_coefficient": 5e-6,
        "density": 1100.0,
        "cost_per_kg": 5.0,
        "max_temp": 400.0,
    },
    "aerogel": {
        "electrical_conductivity": 1e-12,
        "thermal_conductivity": 0.02,
        "seebeck_coefficient": 0.0,
        "density": 100.0,
        "cost_per_kg": 500.0,
        "max_temp": 800.0,
    },
    "silicon": {
        "seebeck_coefficient": 500e-6,
        "electrical_conductivity": 4.0e-4,  # intrinsic; doped is much higher
        "thermal_conductivity": 149.0,
        "density": 2329.0,
        "cost_per_kg": 50.0,
        "max_temp": 1687.0,
    },
}


@dataclass
class Component:
    """One material in one role within a Configuration."""
    material: str
    role: str
    capabilities: List[str] = field(default_factory=list)
    parameters: Dict[str, float] = field(default_factory=dict)


@dataclass
class Configuration:
    """A candidate artifact — the structured output of Stage II.

    See docs/ARTIFACT_SCHEMA.md for the full schema and the config_hash
    invariant.
    """
    config_id: str
    spec_objective: str
    domain: str
    components: List[Component] = field(default_factory=list)
    structure: str = "monolithic"
    parameters: Dict[str, float] = field(default_factory=dict)
    design_operator_chain: List[str] = field(default_factory=list)
    source_capabilities: List[str] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)
    config_hash: str = ""

    # ----- canonicality -------------------------------------------------
    def canonical_dict(self) -> Dict[str, Any]:
        """Return a canonical dict for hashing.

        Excludes config_id, spec_objective (prose), design_operator_chain
        (path), provenance (metadata), and source_capabilities (spec-side).
        Includes only structural + parametric content.
        """
        def _round(v: Any) -> Any:
            if isinstance(v, float):
                # Round to 8 decimals to avoid float drift
                return round(v, 8)
            return v

        comps = []
        for c in self.components:
            comps.append({
                "material": c.material,
                "role": c.role,
                "parameters": {k: _round(v) for k, v in sorted(c.parameters.items())},
            })
        comps.sort(key=lambda x: (x["material"], x["role"]))

        return {
            "domain": self.domain,
            "structure": self.structure,
            "parameters": {k: _round(v) for k, v in sorted(self.parameters.items())},
            "components": comps,
        }

    def compute_hash(self) -> str:
        """Compute the canonical SHA-256 hash (16 hex chars)."""
        canon = self.canonical_dict()
        s = json.dumps(canon, sort_keys=True, default=str)
        return hashlib.sha256(s.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict (for logging / ledger)."""
        return {
            "config_id": self.config_id,
            "spec_objective": self.spec_objective,
            "domain": self.domain,
            "components": [asdict(c) for c in self.components],
            "structure": self.structure,
            "parameters": self.parameters,
            "design_operator_chain": self.design_operator_chain,
            "source_capabilities": self.source_capabilities,
            "provenance": self.provenance,
            "config_hash": self.config_hash,
        }


# ---------------------------------------------------------------------------
# Design operators
# ---------------------------------------------------------------------------
DESIGN_OPERATORS: Tuple[str, ...] = (
    "combine", "replace", "invert", "amplify", "attenuate",
    "split", "merge", "layer", "stabilize", "modulate",
    "substitute", "parameterize",
)


class ArtifactGenerator:
    """Stage II: generates Configuration objects from a Specification.

    Algorithm:
      1. Identify candidate materials from the capability graph (entities
         whose capabilities overlap spec.capability_targets) and from
         spec.target_material.
      2. For each of n configurations:
         a. Pick a base material (deterministic under seed).
         b. Initialize a monolithic Configuration with the base material's
            catalog parameters.
         c. Apply a chain of 2-4 random design operators, each transforming
            the Configuration's components, structure, or parameters.
         d. Compute the canonical config_hash.
      3. Return the list of Configurations.
    """

    OPERATORS: Tuple[str, ...] = DESIGN_OPERATORS

    def __init__(self, seed: int = 42):
        self.seed = seed

    # ----- public API ---------------------------------------------------
    def generate(self, spec, capability_graph, n: int = 5) -> List[Configuration]:
        """Generate n candidate Configurations.

        Args:
            spec: a Specification (see scripts/specification.py)
            capability_graph: a CapabilityGraph (see scripts/capability_graph.py)
            n: number of configurations to generate

        Returns:
            list of Configuration objects, deterministic under self.seed
        """
        rng = random.Random(self.seed)
        candidate_materials = self._find_materials(spec, capability_graph)
        configs: List[Configuration] = []

        for i in range(n):
            base = rng.choice(candidate_materials)
            base_params = dict(MATERIAL_PARAMS.get(base, {}))
            comp = Component(
                material=base,
                role="active",
                capabilities=list(spec.capability_targets),
                parameters=base_params,
            )
            config = Configuration(
                config_id=f"CONFIG-{self.seed:04d}-{i:03d}",
                spec_objective=spec.objective,
                domain=spec.domain,
                components=[comp],
                structure="monolithic",
                parameters={
                    "thickness_m": 1.0e-3,
                    "area_m2": 1.0e-4,
                    # Per cycle 208 (auditor finding): evaluate each material
                    # at its OWN operating temperature from the materials DB,
                    # not a fixed 350K. This prevents systematically undervaluing
                    # high-temperature thermoelectrics like SnSe (ZT=2.6 at 923K
                    # but only ZT≈1.0 at 350K).
                    "T_hot_K": base_params.get("temperature", 400.0) + 50.0,  # hot side = peak T + 50K
                    "T_cold_K": max(300.0, base_params.get("temperature", 400.0) - 50.0),  # cold side = peak T - 50K (min 300K)
                },
                design_operator_chain=["init"],
                source_capabilities=list(spec.capability_targets),
                provenance={
                    "generator": "ArtifactGenerator",
                    "seed": self.seed,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "base_material": base,
                    "candidate_materials": sorted(candidate_materials),
                },
            )

            # Apply a chain of 2-4 operators.
            n_ops = rng.randint(2, 4)
            for _ in range(n_ops):
                op = rng.choice(self.OPERATORS)
                config = self._apply_operator(config, op, rng, candidate_materials)

            config.config_hash = config.compute_hash()
            configs.append(config)

        return configs

    def apply_operator(self, config: Configuration, op: str,
                       rng: Optional[random.Random] = None,
                       materials: Optional[List[str]] = None) -> Configuration:
        """Apply a single design operator to a configuration.

        Public for use by the contradiction solver (Stage III) and tests.
        """
        if rng is None:
            rng = random.Random(self.seed)
        if materials is None:
            materials = list(MATERIAL_PARAMS.keys())
        return self._apply_operator(config, op, rng, materials)

    # ----- internals ----------------------------------------------------
    def _find_materials(self, spec, cg) -> List[str]:
        """Find materials whose capabilities match the spec's targets."""
        materials: List[str] = []
        for cap in spec.capability_targets:
            for entity in cg.get_entities_with_capability(cap):
                # Normalize entity names: "bismuth telluride" → "bismuth_telluride"
                norm = entity.lower().replace(" ", "_")
                if norm in MATERIAL_PARAMS:
                    materials.append(norm)
        # Always include the spec's target material if known
        if spec.target_material:
            tm = spec.target_material.lower().replace(" ", "_")
            if tm in MATERIAL_PARAMS:
                materials.append(tm)
        # Fallback
        if not materials:
            materials = ["bismuth_telluride"]
        return sorted(set(materials))

    def _apply_operator(self, config: Configuration, op: str,
                        rng: random.Random,
                        materials: List[str]) -> Configuration:
        """Apply one design operator. Mutates and returns config."""
        if op == "combine":
            # Append a second material as a secondary-role component.
            other = rng.choice(materials)
            config.components.append(Component(
                material=other,
                role="secondary",
                parameters=dict(MATERIAL_PARAMS.get(other, {})),
            ))

        elif op == "replace":
            if config.components:
                idx = rng.randrange(len(config.components))
                new_mat = rng.choice(materials)
                old_role = config.components[idx].role
                old_caps = config.components[idx].capabilities
                config.components[idx] = Component(
                    material=new_mat,
                    role=old_role,
                    capabilities=list(old_caps),
                    parameters=dict(MATERIAL_PARAMS.get(new_mat, {})),
                )

        elif op == "invert":
            # Invert a parameter — e.g., introduce porosity to slash
            # thermal conductivity (a standard TE strategy).
            if config.components:
                c = config.components[0]
                porosity = round(rng.uniform(0.2, 0.5), 4)
                c.parameters["porosity"] = porosity
                # Effective medium approximation (Loeb model, simplified):
                # k_eff = k_solid * (1 - porosity)
                k0 = c.parameters.get("thermal_conductivity", 1.0)
                c.parameters["thermal_conductivity"] = k0 * (1.0 - porosity)

        elif op == "amplify":
            if config.components:
                c = config.components[0]
                k = round(rng.uniform(1.5, 3.0), 4)
                # F-100: clamp amplified values to physical bounds
                try:
                    from scripts.physical_plausibility import PhysicalPlausibilityChecker
                    _plaus_checker = PhysicalPlausibilityChecker()
                except ImportError:
                    _plaus_checker = None
                for param in ("seebeck_coefficient", "electrical_conductivity"):
                    if param in c.parameters:
                        new_val = c.parameters[param] * k
                        if _plaus_checker:
                            new_val = _plaus_checker.clamp_parameter(param, new_val)
                        c.parameters[param] = new_val

        elif op == "attenuate":
            if config.components:
                c = config.components[0]
                k = round(rng.uniform(0.3, 0.7), 4)
                # F-100: clamp attenuated values to physical bounds
                try:
                    from scripts.physical_plausibility import PhysicalPlausibilityChecker
                    _plaus_checker = PhysicalPlausibilityChecker()
                except ImportError:
                    _plaus_checker = None
                for param in ("thermal_conductivity",):
                    if param in c.parameters:
                        c.parameters[param] = c.parameters[param] * k

        elif op == "split":
            n_seg = rng.randint(2, 5)
            config.parameters["n_segments"] = float(n_seg)
            config.structure = f"segmented_{n_seg}"

        elif op == "merge":
            if len(config.components) >= 2:
                # Merge component 1 into component 0 (keep first material's
                # role but blend parameters by mean).
                c0, c1 = config.components[0], config.components[1]
                merged_params: Dict[str, float] = {}
                keys = set(c0.parameters) | set(c1.parameters)
                for k_ in keys:
                    v0 = c0.parameters.get(k_, 0.0)
                    v1 = c1.parameters.get(k_, 0.0)
                    merged_params[k_] = (v0 + v1) / 2.0
                c0.parameters = merged_params
                config.components = [c0] + config.components[2:]
                config.parameters["merged"] = 1.0

        elif op == "layer":
            n_layers = rng.randint(2, 4)
            config.parameters["n_layers"] = float(n_layers)
            config.structure = f"layered_{n_layers}"

        elif op == "stabilize":
            # Add a polymer stabilizer coating.
            config.parameters["stabilizer"] = 1.0
            config.components.append(Component(
                material="polymer",
                role="stabilizer",
                parameters=dict(MATERIAL_PARAMS["polymer"]),
            ))

        elif op == "modulate":
            # Modulate a parameter periodically (e.g., graded doping).
            freq = round(rng.uniform(0.1, 1.0), 4)
            config.parameters["modulation_freq"] = freq

        elif op == "substitute":
            if config.components:
                c = config.components[0]
                x = round(rng.uniform(0.1, 0.5), 4)
                c.parameters["substitution_fraction"] = x
                other_mat = rng.choice([m for m in materials if m != c.material]
                                       or [c.material])
                other_params = MATERIAL_PARAMS.get(other_mat, {})
                for k_ in list(c.parameters.keys()):
                    if k_ in other_params and isinstance(c.parameters[k_], (int, float)):
                        c.parameters[k_] = (1.0 - x) * c.parameters[k_] + x * other_params[k_]
                # Record the substituent material in the component role
                c.role = f"{c.role}+{other_mat}"

        elif op == "parameterize":
            # Set a global parameter (e.g., thickness).
            config.parameters["thickness_m"] = round(10 ** rng.uniform(-4, -2), 8)

        else:
            raise ValueError(f"unknown design operator: {op}")

        config.design_operator_chain.append(op)
        return config


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
def main():
    """Demo: generate 5 thermoelectric candidates and print them."""
    print("=" * 60)
    print("ARTIFACT GENERATOR (Stage II)")
    print("=" * 60)
    print()

    from scripts.specification import SpecificationEngine
    from scripts.capability_graph import CapabilityGraph

    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    print(f"Spec: {spec.objective}")
    print(f"Domain: {spec.domain}")
    print(f"Targets: {spec.capability_targets}")
    print()

    cg = CapabilityGraph()
    cg.from_relations([
        ("bismuth telluride", "generates", "voltage"),
        ("bismuth telluride", "conducts", "electricity"),
        ("bismuth telluride", "conducts", "heat"),
        ("lead telluride", "generates", "voltage"),
        ("graphene", "conducts", "electricity"),
    ])

    gen = ArtifactGenerator(seed=42)
    configs = gen.generate(spec, cg, n=5)
    print(f"Generated {len(configs)} configurations:")
    for c in configs:
        print(f"\n  {c.config_id}  hash={c.config_hash}")
        print(f"    structure: {c.structure}")
        print(f"    operators: {' -> '.join(c.design_operator_chain)}")
        print(f"    components:")
        for comp in c.components:
            print(f"      - {comp.material} ({comp.role}): "
                  f"{len(comp.parameters)} params")
        print(f"    global params: "
              f"{ {k: round(v,4) if isinstance(v,float) else v for k,v in c.parameters.items()} }")

    # Determinism check
    configs2 = ArtifactGenerator(seed=42).generate(spec, cg, n=5)
    hashes_a = [c.config_hash for c in configs]
    hashes_b = [c.config_hash for c in configs2]
    print()
    print(f"Determinism: {'PASS' if hashes_a == hashes_b else 'FAIL'}")
    print(f"  run 1: {hashes_a}")
    print(f"  run 2: {hashes_b}")


if __name__ == "__main__":
    main()
