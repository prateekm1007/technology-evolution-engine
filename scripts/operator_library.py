#!/usr/bin/env python3
"""
operator_library.py — DR-72: Registry of all 14 design operators.

Each operator is a pure function: (Configuration, **kwargs) -> Configuration.
The 14 operators extend the 12 already in scripts/artifact_generator.py
with `generalize` and `specialize` (which are inverse abstractions):

  Original 12 (from artifact_generator.py):
    combine, replace, invert, amplify, attenuate, split, merge,
    layer, stabilize, modulate, substitute, parameterize

  New in DR-72:
    generalize    — abstract a parameter to a range (generalize a specific
                    thickness into a [min, max] range, e.g., for tolerance
                    stack-up analysis)
    instantiate   — pin a parameter to a specific value (the inverse of
                    generalize; used when a search has settled on a final
                    design)

This module is the canonical registry. The search engine (DR-73) and
the artifact generator (Stage II) MUST import from this module —
adversarial tests verify that deleting this module breaks generation.

Usage:
    from scripts.operator_library import OPERATOR_LIBRARY, apply_operator
    new_config = apply_operator(config, "combine", materials=["graphene"])

    # Or get the registry:
    registry = OPERATOR_LIBRARY
    assert "combine" in registry.names
"""
import sys
import copy
import random
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Callable, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.artifact_generator import (
    Configuration, Component, MATERIAL_PARAMS, ArtifactGenerator,
)


# ---------------------------------------------------------------------------
# Operator metadata
# ---------------------------------------------------------------------------
@dataclass
class OperatorMeta:
    """Metadata describing a single design operator."""
    name: str
    description: str
    arity: str = "unary"          # unary, binary, n-ary
    reversibility: str = "reversible"  # reversible, irreversible
    parameters: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Operator implementations.
# Each takes (config, **kwargs) and returns a NEW Configuration.
# The original config is NOT mutated.
# ---------------------------------------------------------------------------
def _clone(config: Configuration) -> Configuration:
    """Deep-copy a configuration (operators must not mutate inputs)."""
    return copy.deepcopy(config)


def op_combine(config: Configuration, materials: Optional[List[str]] = None,
               **kwargs) -> Configuration:
    """Add a secondary material as a second component."""
    c = _clone(config)
    if not materials:
        materials = list(MATERIAL_PARAMS.keys())
    other = kwargs.get("material") or materials[0]
    c.components.append(Component(
        material=other, role="secondary",
        parameters=dict(MATERIAL_PARAMS.get(other, {})),
    ))
    c.design_operator_chain.append("combine")
    return c


def op_replace(config: Configuration, materials: Optional[List[str]] = None,
               **kwargs) -> Configuration:
    """Replace a component's material with another."""
    c = _clone(config)
    if not c.components:
        c.design_operator_chain.append("replace")
        return c
    if not materials:
        materials = list(MATERIAL_PARAMS.keys())
    idx = kwargs.get("index", 0)
    new_mat = kwargs.get("material") or materials[0]
    if idx >= len(c.components):
        idx = 0
    old_role = c.components[idx].role
    old_caps = list(c.components[idx].capabilities)
    c.components[idx] = Component(
        material=new_mat, role=old_role,
        capabilities=old_caps,
        parameters=dict(MATERIAL_PARAMS.get(new_mat, {})),
    )
    c.design_operator_chain.append("replace")
    return c


def op_invert(config: Configuration, **kwargs) -> Configuration:
    """Invert a parameter (e.g., introduce porosity that lowers κ)."""
    c = _clone(config)
    if not c.components:
        c.design_operator_chain.append("invert")
        return c
    comp = c.components[0]
    porosity = kwargs.get("porosity", 0.3)
    comp.parameters["porosity"] = porosity
    k0 = comp.parameters.get("thermal_conductivity", 1.0)
    comp.parameters["thermal_conductivity"] = k0 * (1.0 - porosity)
    c.design_operator_chain.append("invert")
    return c


def op_amplify(config: Configuration, factor: float = 2.0,
               params: Optional[List[str]] = None, **kwargs) -> Configuration:
    """Multiply selected parameters by a factor > 1.

    Per F-100 (cycle 205): amplified values are CLAMPED to physical bounds
    to prevent unphysical number-gaming (e.g., ZT=16774 from unbounded
    seebeck/σ amplification).
    """
    c = _clone(config)
    if not c.components:
        c.design_operator_chain.append("amplify")
        return c
    if params is None:
        params = ["seebeck_coefficient", "electrical_conductivity"]
    # F-100: import physical bounds and clamp
    try:
        from scripts.physical_plausibility import PhysicalPlausibilityChecker
        checker = PhysicalPlausibilityChecker()
    except ImportError:
        checker = None
    for comp in c.components:
        for p in params:
            if p in comp.parameters and isinstance(comp.parameters[p], (int, float)):
                new_val = comp.parameters[p] * factor
                # F-100: clamp to physical bounds
                if checker:
                    new_val = checker.clamp_parameter(p, new_val)
                comp.parameters[p] = new_val
    c.design_operator_chain.append("amplify")
    return c


def op_attenuate(config: Configuration, factor: float = 0.5,
                 params: Optional[List[str]] = None, **kwargs) -> Configuration:
    """Multiply selected parameters by a factor < 1.

    Per F-100 (cycle 205): attenuated values are CLAMPED to physical bounds.
    """
    c = _clone(config)
    if not c.components:
        c.design_operator_chain.append("attenuate")
        return c
    if params is None:
        params = ["thermal_conductivity"]
    # F-100: import physical bounds and clamp
    try:
        from scripts.physical_plausibility import PhysicalPlausibilityChecker
        checker = PhysicalPlausibilityChecker()
    except ImportError:
        checker = None
    for comp in c.components:
        for p in params:
            if p in comp.parameters and isinstance(comp.parameters[p], (int, float)):
                new_val = comp.parameters[p] * factor
                # F-100: clamp to physical bounds
                if checker:
                    new_val = checker.clamp_parameter(p, new_val)
                comp.parameters[p] = new_val
    c.design_operator_chain.append("attenuate")
    return c


def op_split(config: Configuration, n_segments: int = 3, **kwargs) -> Configuration:
    """Split the configuration into n_segments segments."""
    c = _clone(config)
    c.parameters["n_segments"] = float(n_segments)
    c.structure = f"segmented_{n_segments}"
    c.design_operator_chain.append("split")
    return c


def op_merge(config: Configuration, **kwargs) -> Configuration:
    """Merge the first two components into one (blended parameters)."""
    c = _clone(config)
    if len(c.components) < 2:
        c.design_operator_chain.append("merge")
        return c
    c0, c1 = c.components[0], c.components[1]
    keys = set(c0.parameters) | set(c1.parameters)
    merged = {}
    for k in keys:
        v0 = c0.parameters.get(k, 0.0)
        v1 = c1.parameters.get(k, 0.0)
        merged[k] = (v0 + v1) / 2.0
    c0.parameters = merged
    c.components = [c0] + c.components[2:]
    c.parameters["merged"] = 1.0
    c.design_operator_chain.append("merge")
    return c


def op_layer(config: Configuration, n_layers: int = 3, **kwargs) -> Configuration:
    """Layer the configuration into n_layers."""
    c = _clone(config)
    c.parameters["n_layers"] = float(n_layers)
    c.structure = f"layered_{n_layers}"
    c.design_operator_chain.append("layer")
    return c


def op_stabilize(config: Configuration, stabilizer: str = "polymer",
                 **kwargs) -> Configuration:
    """Add a stabilizer component."""
    c = _clone(config)
    c.parameters["stabilizer"] = 1.0
    c.components.append(Component(
        material=stabilizer, role="stabilizer",
        parameters=dict(MATERIAL_PARAMS.get(stabilizer, {})),
    ))
    c.design_operator_chain.append("stabilize")
    return c


def op_modulate(config: Configuration, frequency: float = 0.5,
                **kwargs) -> Configuration:
    """Modulate a parameter periodically (e.g., graded doping)."""
    c = _clone(config)
    c.parameters["modulation_freq"] = float(frequency)
    c.design_operator_chain.append("modulate")
    return c


def op_substitute(config: Configuration, materials: Optional[List[str]] = None,
                  fraction: float = 0.2, **kwargs) -> Configuration:
    """Substitute a fraction of the primary component with another material."""
    c = _clone(config)
    if not c.components:
        c.design_operator_chain.append("substitute")
        return c
    if not materials:
        materials = list(MATERIAL_PARAMS.keys())
    other_mat = kwargs.get("material") or (materials[1] if len(materials) > 1
                                           else materials[0])
    comp = c.components[0]
    comp.parameters["substitution_fraction"] = fraction
    other_params = MATERIAL_PARAMS.get(other_mat, {})
    for k in list(comp.parameters.keys()):
        if k in other_params and isinstance(comp.parameters[k], (int, float)):
            comp.parameters[k] = ((1.0 - fraction) * comp.parameters[k]
                                  + fraction * other_params[k])
    comp.role = f"{comp.role}+{other_mat}"
    c.design_operator_chain.append("substitute")
    return c


def op_parameterize(config: Configuration, parameter: str = "thickness_m",
                    value: float = 1e-3, **kwargs) -> Configuration:
    """Set a global parameter to a specific value."""
    c = _clone(config)
    c.parameters[parameter] = float(value)
    c.design_operator_chain.append("parameterize")
    return c


# ---- NEW in DR-72 --------------------------------------------------------
def op_generalize(config: Configuration, parameter: str = "thickness_m",
                  low: float = 0.5e-3, high: float = 5e-3,
                  **kwargs) -> Configuration:
    """Abstract a specific parameter value into a [low, high] range.

    This is the inverse of `instantiate`. Used when the search has
    identified a parameter as a free variable to be explored over a
    range rather than pinned to one value.
    """
    c = _clone(config)
    c.parameters[f"{parameter}_range"] = [float(low), float(high)]
    # Remove the pinned value (if present) — it's now a range
    c.parameters.pop(parameter, None)
    c.design_operator_chain.append("generalize")
    return c


def op_instantiate(config: Configuration, parameter: str = "thickness_m",
                   value: float = 1e-3, **kwargs) -> Configuration:
    """Pin a generalized range to a specific value.

    The inverse of `generalize`. Used when the search has converged on
    a specific design point.
    """
    c = _clone(config)
    c.parameters[parameter] = float(value)
    # Remove any existing range for this parameter
    c.parameters.pop(f"{parameter}_range", None)
    c.design_operator_chain.append("instantiate")
    return c


# ---------------------------------------------------------------------------
# The canonical registry.
# ---------------------------------------------------------------------------
@dataclass
class OperatorLibrary:
    """The canonical registry of all 14 design operators."""
    operators: Dict[str, Callable[..., Configuration]] = field(default_factory=dict)
    metadata: Dict[str, OperatorMeta] = field(default_factory=dict)

    @property
    def names(self) -> List[str]:
        return sorted(self.operators.keys())

    def register(self, name: str, fn: Callable[..., Configuration],
                 meta: OperatorMeta) -> None:
        self.operators[name] = fn
        self.metadata[name] = meta

    def apply(self, config: Configuration, name: str,
              **kwargs) -> Configuration:
        """Apply a named operator to a config."""
        if name not in self.operators:
            raise KeyError(f"unknown operator: {name!r}. "
                           f"Known: {self.names}")
        new_config = self.operators[name](config, **kwargs)
        # Recompute the hash because parameters may have changed
        new_config.config_hash = new_config.compute_hash()
        return new_config

    def apply_chain(self, config: Configuration,
                    chain: List[Tuple[str, Dict[str, Any]]]) -> Configuration:
        """Apply a sequence of (operator_name, kwargs) pairs in order."""
        c = config
        for name, kwargs in chain:
            c = self.apply(c, name, **kwargs)
        return c

    def all_operators_on(self, config: Configuration,
                         **shared_kwargs) -> Dict[str, Configuration]:
        """Apply every operator to the config (returns one per operator)."""
        return {name: self.apply(config, name, **shared_kwargs)
                for name in self.names}


def _build_default_library() -> OperatorLibrary:
    lib = OperatorLibrary()
    specs = [
        ("combine", op_combine, "Add a secondary material as a new component."),
        ("replace", op_replace, "Replace a component's material."),
        ("invert", op_invert, "Invert a parameter (e.g., porosity → lower κ)."),
        ("amplify", op_amplify, "Scale selected parameters UP."),
        ("attenuate", op_attenuate, "Scale selected parameters DOWN."),
        ("split", op_split, "Split the design into n segments."),
        ("merge", op_merge, "Merge two components into one."),
        ("layer", op_layer, "Layer the design into n layers."),
        ("stabilize", op_stabilize, "Add a stabilizer component."),
        ("modulate", op_modulate, "Modulate a parameter periodically."),
        ("substitute", op_substitute, "Substitute a fraction of a material."),
        ("parameterize", op_parameterize, "Set a global parameter."),
        ("generalize", op_generalize, "Abstract a parameter into a range."),
        ("instantiate", op_instantiate, "Pin a parameter to a specific value."),
    ]
    for name, fn, desc in specs:
        lib.register(name, fn, OperatorMeta(
            name=name, description=desc))
    return lib


# The canonical, singleton registry.
OPERATOR_LIBRARY: OperatorLibrary = _build_default_library()


# ---------------------------------------------------------------------------
# Convenience top-level functions
# ---------------------------------------------------------------------------
def apply_operator(config: Configuration, name: str,
                   **kwargs) -> Configuration:
    """Apply a named operator (using the canonical registry)."""
    return OPERATOR_LIBRARY.apply(config, name, **kwargs)


def list_operators() -> List[str]:
    """Return the list of all registered operator names."""
    return OPERATOR_LIBRARY.names


def generate_with_library(spec, capability_graph, n: int = 5,
                          seed: int = 42) -> List[Configuration]:
    """Generate candidates using OPERATOR_LIBRARY instead of the
    artifact_generator's internal operator table.

    This is the adversarial entry point: if OPERATOR_LIBRARY is deleted
    or empty, generation MUST fail. Used by tests/test_operator_library.py
    to verify that the library is load-bearing.
    """
    if not OPERATOR_LIBRARY.operators:
        raise RuntimeError("OPERATOR_LIBRARY is empty or missing — "
                           "generation cannot proceed.")
    # Use the artifact generator to get base configs (no operators applied),
    # then apply random operators from the library.
    rng = random.Random(seed)
    # Build a single-component base configuration per material
    base_materials: List[str] = []
    for cap in spec.capability_targets:
        for entity in capability_graph.get_entities_with_capability(cap):
            norm = entity.lower().replace(" ", "_")
            if norm in MATERIAL_PARAMS:
                base_materials.append(norm)
    if spec.target_material:
        tm = spec.target_material.lower().replace(" ", "_")
        if tm in MATERIAL_PARAMS:
            base_materials.append(tm)
    if not base_materials:
        base_materials = ["bismuth_telluride"]

    base_materials = sorted(set(base_materials))
    configs: List[Configuration] = []
    for i in range(n):
        base = rng.choice(base_materials)
        comp = Component(
            material=base, role="active",
            capabilities=list(spec.capability_targets),
            parameters=dict(MATERIAL_PARAMS.get(base, {})),
        )
        config = Configuration(
            config_id=f"LIB-{seed:04d}-{i:03d}",
            spec_objective=spec.objective,
            domain=spec.domain,
            components=[comp],
            structure="monolithic",
            parameters={
                "thickness_m": 1.0e-3,
                "area_m2": 1.0e-4,
                "T_hot_K": 400.0,
                "T_cold_K": 300.0,
            },
            design_operator_chain=["init"],
            source_capabilities=list(spec.capability_targets),
            provenance={
                "generator": "operator_library.generate_with_library",
                "seed": seed,
                "base_material": base,
            },
        )
        # Apply 2-4 random operators from the library
        n_ops = rng.randint(2, 4)
        for _ in range(n_ops):
            op_name = rng.choice(OPERATOR_LIBRARY.names)
            config = OPERATOR_LIBRARY.apply(config, op_name)
        configs.append(config)
    return configs


def main():
    print("=" * 60)
    print("OPERATOR LIBRARY (DR-72)")
    print("=" * 60)
    print()

    print(f"Registered operators ({len(OPERATOR_LIBRARY.names)}):")
    for name in OPERATOR_LIBRARY.names:
        meta = OPERATOR_LIBRARY.metadata[name]
        print(f"  {name:15s}  {meta.description}")
    print()

    # Build a base config
    from scripts.specification import SpecificationEngine
    from scripts.capability_graph import CapabilityGraph
    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([("bismuth telluride", "generates", "voltage")])

    base = Component(material="bismuth_telluride", role="active",
                     parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))
    config = Configuration(
        config_id="DEMO", spec_objective="x", domain="thermoelectric",
        components=[base], structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    config.config_hash = config.compute_hash()

    print("Apply each operator once:")
    for name in OPERATOR_LIBRARY.names:
        new = OPERATOR_LIBRARY.apply(config, name)
        print(f"  {name:15s} → hash={new.config_hash}  "
              f"chain={new.design_operator_chain[-1]}")

    print()
    print("Generate 3 candidates via the library:")
    configs = generate_with_library(spec, cg, n=3, seed=42)
    for c in configs:
        print(f"  {c.config_id}  hash={c.config_hash}  "
              f"chain={c.design_operator_chain}")


if __name__ == "__main__":
    main()
