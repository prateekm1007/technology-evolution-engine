#!/usr/bin/env python3
"""
constraint_pruning.py — DR-73: Prune candidates that violate hard constraints.

A "hard constraint" is a physics or manufacturing limit that a candidate
MUST satisfy to be worth exploring further. Candidates that violate any
hard constraint are pruned BEFORE expansion (to save search budget).

This module wraps:
  - capability_constraints (DR-69): physics constraints from capabilities
  - prototype_compiler manufacturing constraints (Stage VI): min feature
    size, max layers, cost ceiling, etc.
  - any user-supplied constraints

Usage:
    from scripts.constraint_pruning import ConstraintPruner
    pruner = ConstraintPruner()
    result = pruner.prune(configurations, capabilities_per_config)
    # result.survived = [...], result.pruned = [...]
"""
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Callable, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.artifact_generator import Configuration, MATERIAL_PARAMS
from scripts.capability_constraints import CapabilityConstraints


@dataclass
class ConstraintCheck:
    """The result of checking one constraint on one candidate."""
    constraint_name: str
    passed: bool
    actual: Any = None
    expected: Any = None
    message: str = ""


@dataclass
class PruneResult:
    """The result of pruning a batch of candidates."""
    survived: List[Configuration] = field(default_factory=list)
    pruned: List[Tuple[Configuration, List[ConstraintCheck]]] = field(default_factory=list)
    n_input: int = 0
    n_survived: int = 0
    n_pruned: int = 0
    checks_per_survivor: Dict[str, List[ConstraintCheck]] = field(default_factory=dict)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_input": self.n_input,
            "n_survived": self.n_survived,
            "n_pruned": self.n_pruned,
            "survived_ids": [c.config_id for c in self.survived],
            "pruned_ids": [c.config_id for c, _ in self.pruned],
            "prune_reasons": {
                c.config_id: [chk.__dict__ for chk in checks]
                for c, checks in self.pruned
            },
            "timestamp": self.timestamp,
        }


class ConstraintPruner:
    """DR-73: prunes candidates that violate hard constraints."""

    def __init__(self,
                 manufacturing_constraints: Optional[Dict[str, Any]] = None,
                 capability_constraints: Optional[CapabilityConstraints] = None,
                 custom_checkers: Optional[List[Callable[[Configuration], ConstraintCheck]]] = None):
        self.manufacturing_constraints: Dict[str, Any] = {
            "min_feature_size_m": 1.0e-5,
            "max_layers": 10,
            "max_operating_temp_K": 800.0,
            "allowed_materials": list(MATERIAL_PARAMS.keys()),
            "cost_ceiling_usd": 1000.0,
            "max_component_count": 8,
        }
        if manufacturing_constraints:
            self.manufacturing_constraints.update(manufacturing_constraints)
        self.capability_constraints = (
            capability_constraints or CapabilityConstraints())
        self.custom_checkers: List[Callable[[Configuration], ConstraintCheck]] = (
            list(custom_checkers) if custom_checkers else [])

    # ----- public API ---------------------------------------------------
    def prune(self, configs: List[Configuration],
              capabilities_per_config: Optional[Dict[str, List[str]]] = None
              ) -> PruneResult:
        """Prune a batch of candidates by hard constraints.

        Args:
            configs: list of Configurations to check
            capabilities_per_config: optional dict {config_id: [cap, ...]}
                — used to derive physics constraints per candidate

        Returns:
            PruneResult with survived and pruned lists
        """
        capabilities_per_config = capabilities_per_config or {}
        survived: List[Configuration] = []
        pruned: List[Tuple[Configuration, List[ConstraintCheck]]] = []
        checks_per_survivor: Dict[str, List[ConstraintCheck]] = {}

        for c in configs:
            checks = self._check_all(c, capabilities_per_config.get(c.config_id, []))
            failures = [chk for chk in checks if not chk.passed]
            if failures:
                pruned.append((c, failures))
            else:
                survived.append(c)
                checks_per_survivor[c.config_id] = checks

        return PruneResult(
            survived=survived,
            pruned=pruned,
            n_input=len(configs),
            n_survived=len(survived),
            n_pruned=len(pruned),
            checks_per_survivor=checks_per_survivor,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def add_checker(self, fn: Callable[[Configuration], ConstraintCheck]) -> None:
        """Add a custom constraint checker."""
        self.custom_checkers.append(fn)

    # ----- internals ----------------------------------------------------
    def _check_all(self, config: Configuration,
                   capabilities: List[str]) -> List[ConstraintCheck]:
        checks: List[ConstraintCheck] = []
        # 1. Manufacturing constraints
        checks.extend(self._check_manufacturing(config))
        # 2. Capability-derived physics constraints
        if capabilities:
            checks.extend(self._check_capability_constraints(config, capabilities))
        # 3. Custom checkers
        for fn in self.custom_checkers:
            checks.append(fn(config))
        return checks

    def _check_manufacturing(self, config: Configuration) -> List[ConstraintCheck]:
        checks: List[ConstraintCheck] = []
        mc = self.manufacturing_constraints

        # Min feature size
        L = config.parameters.get("thickness_m", 1e-3)
        min_size = mc["min_feature_size_m"]
        checks.append(ConstraintCheck(
            constraint_name="min_feature_size",
            passed=L >= min_size,
            actual=L, expected=f">= {min_size}",
            message=(f"thickness {L} < min {min_size}"
                     if L < min_size else "OK"),
        ))

        # Max layers
        n_layers = int(config.parameters.get("n_layers", 1))
        max_lay = mc["max_layers"]
        checks.append(ConstraintCheck(
            constraint_name="max_layers",
            passed=n_layers <= max_lay,
            actual=n_layers, expected=f"<= {max_lay}",
            message=(f"n_layers {n_layers} > max {max_lay}"
                     if n_layers > max_lay else "OK"),
        ))

        # Max operating temperature
        T_hot = config.parameters.get("T_hot_K", 300.0)
        max_T = mc["max_operating_temp_K"]
        checks.append(ConstraintCheck(
            constraint_name="max_operating_temp",
            passed=T_hot <= max_T,
            actual=T_hot, expected=f"<= {max_T}",
            message=(f"T_hot {T_hot} > max {max_T}"
                     if T_hot > max_T else "OK"),
        ))

        # Allowed materials
        allowed = set(mc["allowed_materials"])
        for comp in config.components:
            checks.append(ConstraintCheck(
                constraint_name=f"allowed_material:{comp.material}",
                passed=comp.material in allowed,
                actual=comp.material,
                expected=f"in {sorted(allowed)}",
                message=("OK" if comp.material in allowed
                         else f"{comp.material} not in allowed list"),
            ))

        # Max component count
        max_cc = mc["max_component_count"]
        checks.append(ConstraintCheck(
            constraint_name="max_component_count",
            passed=len(config.components) <= max_cc,
            actual=len(config.components),
            expected=f"<= {max_cc}",
            message=(f"{len(config.components)} > {max_cc}"
                     if len(config.components) > max_cc else "OK"),
        ))

        return checks

    def _check_capability_constraints(self, config: Configuration,
                                       capabilities: List[str]) -> List[ConstraintCheck]:
        """Check capability-derived constraints against the config's parameters."""
        checks: List[ConstraintCheck] = []
        # Flatten all component parameters into one dict for checking
        params: Dict[str, float] = {}
        for comp in config.components:
            for k, v in comp.parameters.items():
                if isinstance(v, (int, float)):
                    params.setdefault(k, v)
        for k, v in config.parameters.items():
            if isinstance(v, (int, float)):
                params.setdefault(k, v)

        result = self.capability_constraints.check_candidate(capabilities, params)
        for v in result["violations"]:
            checks.append(ConstraintCheck(
                constraint_name=f"capability:{v['capability']}",
                passed=False,
                actual=v["value"],
                expected=f"{v['operator']} {v['threshold']} {v['units']}",
                message=(f"{v['parameter']}={v['value']} violates "
                         f"{v['capability']} constraint "
                         f"{v['operator']} {v['threshold']}"),
            ))
        return checks


def main():
    print("=" * 60)
    print("CONSTRAINT PRUNING (DR-73)")
    print("=" * 60)
    print()

    from scripts.specification import SpecificationEngine
    from scripts.capability_graph import CapabilityGraph
    from scripts.artifact_generator import ArtifactGenerator

    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([("bismuth telluride", "generates", "voltage")])
    configs = ArtifactGenerator(seed=42).generate(spec, cg, n=10)

    pruner = ConstraintPruner()
    result = pruner.prune(configs,
                          capabilities_per_config={
                              c.config_id: ["conducts_electricity", "transfers_heat"]
                              for c in configs
                          })
    print(f"Input: {result.n_input}")
    print(f"Survived: {result.n_survived}")
    print(f"Pruned: {result.n_pruned}")
    for c, checks in result.pruned[:3]:
        print(f"  PRUNED {c.config_id}:")
        for chk in checks:
            if not chk.passed:
                print(f"    - {chk.constraint_name}: {chk.message}")


if __name__ == "__main__":
    main()
