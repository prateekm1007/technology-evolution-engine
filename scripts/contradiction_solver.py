#!/usr/bin/env python3
"""
contradiction_solver.py — Stage III: Resolve contradictions with TRIZ
and design operators.

Takes a contradiction (e.g., "increase conductivity → decrease
stability") and a base Configuration, and produces at least one NEW
candidate Configuration that attempts to break the trade-off using
TRIZ principles mapped EXPLICITLY to design operators.

The mapping (TRIZ principle number → design operator name) is a
first-class table in this module. Each TRIZ principle is mapped to
one or more of the 12 design operators defined in
scripts/artifact_generator.py:

    combine, replace, invert, amplify, attenuate, split, merge,
    layer, stabilize, modulate, substitute, parameterize

Algorithm:
  1. Classify (improve, worsen) parameters into physical domains
     (reused from scripts.contradiction_resolver_v2).
  2. Rank all 40 TRIZ principles by physical-domain compatibility.
  3. Map the top-K principles to design operators using TRIZ_TO_OPERATORS.
  4. Apply each mapped operator to the base Configuration, producing
     a new Configuration whose design_operator_chain records the
     TRIZ principle that drove the transformation.
  5. Return a Resolution with the new Configuration(s) and the
     explicit principle → operator mapping.

Usage:
    from scripts.contradiction_solver import ContradictionSolver, Contradiction
    from scripts.artifact_generator import ArtifactGenerator
    base = ArtifactGenerator(seed=42).generate(spec, cg, n=1)[0]
    solver = ContradictionSolver()
    resolution = solver.solve(base, improve="conductivity", worsen="stability")
    # resolution.new_configurations is non-empty
"""
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.artifact_generator import (
    ArtifactGenerator, Configuration, Component, MATERIAL_PARAMS,
    DESIGN_OPERATORS,
)
# Reuse the existing physical-domain classification & TRIZ tables.
from scripts.contradiction_resolver_v2 import (
    PhysicalDomainResolver, PhysicalDomain, PRINCIPLE_DOMAINS,
)


# ---------------------------------------------------------------------------
# Explicit TRIZ principle → design operator mapping.
# This is the table the auditor demanded: each TRIZ principle is mapped
# to one or more design operators. The mapping is grounded in what each
# principle MEANS operationally:
#
#   Segmentation (1) → split the component into modules
#   Taking out (2)   → replace the interfering part
#   Local quality (3) → layer (different layers do different jobs)
#   Merging (5)      → merge
#   Composite materials (40) → combine
#   Porous materials (31) → invert (porosity flips conductivity κ)
#   Parameter changes (35) → parameterize
#   Other way round (13) → invert (flip the function)
#   Dynamicity (15)  → modulate
#   Homogeneity (33) → substitute (use a single material)
#   Phase transitions (36) → substitute (PCM)
#   Preliminary anti-action (9) → amplify
#   Partial/excessive (16) → attenuate
#   Self-service (25) → stabilize (self-regulating stabilizer)
#   Beforehand cushioning (11) → stabilize
#   Preliminary action (10) → parameterize
#   Equipotentiality (12) → parameterize
#   Asymmetry (4) → parameterize
#   Spheroidality (14) → parameterize
#   Continuity (20) → parameterize
#   Skipping (21) → parameterize
#   Color changes (32) → parameterize
#   Thermal expansion (37) → parameterize
#   Another dimension (17) → layer
#   Nested doll (7) → layer
#   Flexible shells (30) → layer
#   Universality (6) → combine
#   Anti-weight (8) → combine
#   Intermediary (24) → combine
#   Mechanics substitution (28) → replace
#   Discarding/recovering (34) → replace
#   Convert harm (22) → substitute
#   Copying (26) → substitute
#   Cheap short-lived (27) → substitute
#   Pneumatics/hydraulics (29) → substitute
#   Strong oxidants (38) → substitute
#   Inert atmosphere (39) → substitute
#   Mechanical vibration (18) → modulate
#   Periodic action (19) → modulate
#   Feedback (23) → modulate
# ---------------------------------------------------------------------------
TRIZ_TO_OPERATORS: Dict[int, List[str]] = {
    1:  ["split"],
    2:  ["replace"],
    3:  ["layer"],
    4:  ["parameterize"],
    5:  ["merge"],
    6:  ["combine"],
    7:  ["layer"],
    8:  ["combine"],
    9:  ["amplify"],
    10: ["parameterize"],
    11: ["stabilize"],
    12: ["parameterize"],
    13: ["invert"],
    14: ["parameterize"],
    15: ["modulate"],
    16: ["attenuate"],
    17: ["layer"],
    18: ["modulate"],
    19: ["modulate"],
    20: ["parameterize"],
    21: ["parameterize"],
    22: ["substitute"],
    23: ["modulate"],
    24: ["combine"],
    25: ["stabilize"],
    26: ["substitute"],
    27: ["substitute"],
    28: ["replace"],
    29: ["substitute"],
    30: ["layer"],
    31: ["invert"],
    32: ["parameterize"],
    33: ["substitute"],
    34: ["replace"],
    35: ["parameterize"],
    36: ["substitute"],
    37: ["parameterize"],
    38: ["substitute"],
    39: ["substitute"],
    40: ["combine"],
}

# Sanity check: every TRIZ principle 1..40 is mapped.
assert all(i in TRIZ_TO_OPERATORS for i in range(1, 41)), \
    "every TRIZ principle must map to at least one design operator"

# Sanity check: every operator name is one of the 12 canonical operators.
_allowed_ops = set(DESIGN_OPERATORS)
assert all(op in _allowed_ops
           for ops in TRIZ_TO_OPERATORS.values() for op in ops), \
    "every TRIZ-mapped operator must be one of the 12 design operators"


# ---------------------------------------------------------------------------
# Parameter → design operator hint
# When the improve/worsen parameter is known, we can give an extra nudge
# toward a specific operator. E.g., "thermal_conductivity" worsens →
# the invert operator (introduce porosity) is especially apt.
# ---------------------------------------------------------------------------
PARAM_TO_OPERATOR_HINT: Dict[str, str] = {
    "thermal_conductivity": "invert",   # porosity slashes κ
    "electrical_conductivity": "amplify",  # boost σ
    "seebeck_coefficient": "amplify",
    "stability": "stabilize",
    "cost": "substitute",
    "weight": "attenuate",  # less material
    "thermal_expansion": "layer",
}


@dataclass
class Contradiction:
    """A contradiction to be resolved.

    Attributes:
        improve: the parameter to improve (e.g., "conductivity")
        worsen: the parameter that worsens (e.g., "stability")
        context: optional context (e.g., "thermoelectric leg")
        base_config: the base Configuration to transform
    """
    improve: str
    worsen: str
    context: str = ""
    base_config: Optional[Configuration] = None


@dataclass
class ResolutionStep:
    """One TRIZ-driven transformation step."""
    principle_number: int
    principle_name: str
    compatibility_score: float
    design_operators: List[str]            # operators mapped from this principle
    applied_operators: List[str]           # operators actually applied
    new_config_id: str
    new_config_hash: str
    reasoning: str


@dataclass
class Resolution:
    """The output of ContradictionSolver.solve()."""
    contradiction: Dict[str, Any]           # {improve, worsen, context}
    base_config_id: str
    base_config_hash: str
    steps: List[ResolutionStep] = field(default_factory=list)
    new_configurations: List[Configuration] = field(default_factory=list)
    timestamp: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contradiction": self.contradiction,
            "base_config_id": self.base_config_id,
            "base_config_hash": self.base_config_hash,
            "steps": [asdict(s) for s in self.steps],
            "new_configurations": [c.to_dict() for c in self.new_configurations],
            "timestamp": self.timestamp,
            "provenance": self.provenance,
        }


class ContradictionSolver:
    """Stage III: resolve contradictions using TRIZ → design operators.

    Pipeline:
      1. Use the existing PhysicalDomainResolver to rank TRIZ principles
         by physical-domain compatibility with the contradiction.
      2. For each of the top-K principles, look up its design operator(s)
         in TRIZ_TO_OPERATORS.
      3. Apply the operator(s) to a COPY of the base Configuration,
         producing a new Configuration.
      4. Return a Resolution containing all new Configurations.
    """

    def __init__(self, seed: int = 42, top_k: int = 3):
        self.seed = seed
        self.top_k = top_k
        self.domain_resolver = PhysicalDomainResolver()
        self.generator = ArtifactGenerator(seed=seed)

    # ----- public API ---------------------------------------------------
    def solve(self, base_config: Configuration,
              improve: str, worsen: str,
              context: str = "") -> Resolution:
        """Resolve a contradiction by applying TRIZ-mapped operators.

        Args:
            base_config: the Configuration to improve
            improve: parameter to improve (e.g., "conductivity")
            worsen: parameter that worsens (e.g., "stability")
            context: optional context string

        Returns:
            a Resolution with at least one new Configuration
        """
        # Rank TRIZ principles by physical-domain compatibility.
        solutions = self.domain_resolver.resolve(
            improve, worsen, context, top_k=self.top_k)

        steps: List[ResolutionStep] = []
        new_configs: List[Configuration] = []

        # Apply each TRIZ principle's mapped operator(s) to the base config.
        # We ALSO consult PARAM_TO_OPERATOR_HINT — if the hint applies, we
        # prepend the hinted operator (because it directly targets the
        # worsened parameter).
        for sol in solutions:
            ops_for_principle = list(TRIZ_TO_OPERATORS.get(sol.principle_number, []))

            # Add the parameter-specific hint as a SECONDARY operator if not already present.
            hint_improve = PARAM_TO_OPERATOR_HINT.get(improve.lower())
            hint_worsen = PARAM_TO_OPERATOR_HINT.get(worsen.lower())
            hint = hint_improve or hint_worsen
            applied: List[str] = []
            if hint and hint not in ops_for_principle:
                applied.append(hint)
            applied.extend(ops_for_principle)

            # Build a new Configuration by copying the base and applying
            # each operator in turn.
            new_config = self._copy_config(base_config, suffix=f"-T{sol.principle_number}")
            new_config.provenance = {
                **dict(base_config.provenance),
                "transformed_by": "ContradictionSolver",
                "triz_principle": sol.principle_number,
                "triz_principle_name": sol.principle_name,
                "design_operators": applied,
                "contradiction_improve": improve,
                "contradiction_worsen": worsen,
                "seed": self.seed,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            for op in applied:
                new_config = self.generator.apply_operator(
                    new_config, op,
                    materials=list(MATERIAL_PARAMS.keys()))
            # Re-tag the chain to record the TRIZ principle inline.
            new_config.design_operator_chain.append(
                f"triz:{sol.principle_number}({sol.principle_name})")
            new_config.config_hash = new_config.compute_hash()

            new_configs.append(new_config)
            steps.append(ResolutionStep(
                principle_number=sol.principle_number,
                principle_name=sol.principle_name,
                compatibility_score=sol.compatibility_score,
                design_operators=ops_for_principle,
                applied_operators=applied,
                new_config_id=new_config.config_id,
                new_config_hash=new_config.config_hash,
                reasoning=(
                    f"Contradiction (improve {improve}, worsen {worsen}) "
                    f"is in domains "
                    f"{[d for d in [self.domain_resolver.classify_parameter(improve).value,
                                    self.domain_resolver.classify_parameter(worsen).value]]}. "
                    f"Principle {sol.principle_number} ({sol.principle_name}) "
                    f"has compatibility {sol.compatibility_score:.2f} and maps "
                    f"to design operator(s) {ops_for_principle}. "
                    f"Applied: {applied}."
                ),
            ))

        return Resolution(
            contradiction={"improve": improve, "worsen": worsen, "context": context},
            base_config_id=base_config.config_id,
            base_config_hash=base_config.config_hash,
            steps=steps,
            new_configurations=new_configs,
            timestamp=datetime.now(timezone.utc).isoformat(),
            provenance={
                "solver": "ContradictionSolver",
                "stage": "III",
                "method": "TRIZ → design operator mapping",
                "triz_mapping_table": "TRIZ_TO_OPERATORS (40 principles → 12 operators)",
                "seed": self.seed,
            },
        )

    def resolve(self, base_config: Configuration, improve: str, worsen: str,
                context: str = "") -> Resolution:
        """Alias for solve() (matches the existing resolver naming)."""
        return self.solve(base_config, improve, worsen, context)

    # ----- mapping accessors -------------------------------------------
    @staticmethod
    def get_operators_for_principle(principle_number: int) -> List[str]:
        """Return the design operator(s) mapped to a TRIZ principle."""
        return list(TRIZ_TO_OPERATORS.get(principle_number, []))

    @staticmethod
    def get_principles_for_operator(operator_name: str) -> List[int]:
        """Return all TRIZ principles that map to a given operator."""
        return [pnum for pnum, ops in TRIZ_TO_OPERATORS.items()
                if operator_name in ops]

    @staticmethod
    def all_principles_mapped() -> bool:
        """Verify that all 40 TRIZ principles are mapped to operators."""
        return all(i in TRIZ_TO_OPERATORS for i in range(1, 41))

    # ----- internals ----------------------------------------------------
    def _copy_config(self, config: Configuration,
                     suffix: str = "") -> Configuration:
        """Deep-copy a Configuration (so we don't mutate the base)."""
        new_components = [Component(
            material=c.material,
            role=c.role,
            capabilities=list(c.capabilities),
            parameters=dict(c.parameters),
        ) for c in config.components]
        return Configuration(
            config_id=config.config_id + suffix,
            spec_objective=config.spec_objective,
            domain=config.domain,
            components=new_components,
            structure=config.structure,
            parameters=dict(config.parameters),
            design_operator_chain=list(config.design_operator_chain),
            source_capabilities=list(config.source_capabilities),
            provenance=dict(config.provenance),
            config_hash="",  # recomputed later
        )


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
def main():
    """Demo: resolve a conductivity-vs-stability contradiction."""
    print("=" * 60)
    print("CONTRADICTION SOLVER (Stage III)")
    print("=" * 60)
    print()

    from scripts.specification import SpecificationEngine
    from scripts.capability_graph import CapabilityGraph

    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([
        ("bismuth telluride", "generates", "voltage"),
        ("bismuth telluride", "conducts", "electricity"),
    ])
    base = ArtifactGenerator(seed=42).generate(spec, cg, n=1)[0]
    print(f"Base config: {base.config_id}  hash={base.config_hash}")
    print(f"  operators: {' -> '.join(base.design_operator_chain)}")
    print(f"  structure: {base.structure}")
    print(f"  components: {[(c.material, c.role) for c in base.components]}")
    print()

    solver = ContradictionSolver(seed=42, top_k=3)

    print("Test 1: improve conductivity, worsen stability")
    resolution = solver.solve(base, improve="conductivity", worsen="stability",
                              context="thermoelectric leg")
    print(f"  Generated {len(resolution.new_configurations)} new configurations:")
    for step, new_c in zip(resolution.steps, resolution.new_configurations):
        print(f"\n    Principle {step.principle_number} ({step.principle_name}) "
              f"— compatibility {step.compatibility_score:.2f}")
        print(f"      Mapped operators: {step.design_operators}")
        print(f"      Applied operators: {step.applied_operators}")
        print(f"      New config: {new_c.config_id}  hash={new_c.config_hash}")
        print(f"      New chain: {' -> '.join(new_c.design_operator_chain)}")
        print(f"      New structure: {new_c.structure}")
        print(f"      New components: {[(c.material, c.role) for c in new_c.components]}")
    print()
    print(f"  Provenance: {resolution.provenance}")

    print()
    print("Test 2: improve thermal_conductivity (lower is better), worsen cost")
    # NOTE: in thermoelectrics, LOWER κ is better. We model the
    # contradiction as "improve thermal_conductivity" → the solver
    # applies invert (porosity) which reduces κ.
    resolution2 = solver.solve(base, improve="thermal_conductivity",
                                worsen="cost", context="thermoelectric leg")
    print(f"  Generated {len(resolution2.new_configurations)} new configurations.")
    for step, new_c in zip(resolution2.steps, resolution2.new_configurations):
        # Verify that the invert operator (when applied) reduced κ
        new_kappa = new_c.components[0].parameters.get("thermal_conductivity")
        base_kappa = base.components[0].parameters.get("thermal_conductivity")
        if "invert" in step.applied_operators and new_kappa and base_kappa:
            print(f"    Principle {step.principle_number} ({step.principle_name}) "
                  f"→ invert: κ {base_kappa:.3f} → {new_kappa:.3f} "
                  f"(reduced: {new_kappa < base_kappa})")

    print()
    print(f"All 40 TRIZ principles mapped? {ContradictionSolver.all_principles_mapped()}")
    print(f"Operators for principle 40 (Composite): "
          f"{ContradictionSolver.get_operators_for_principle(40)}")
    print(f"Principles that map to 'layer': "
          f"{ContradictionSolver.get_principles_for_operator('layer')}")


if __name__ == "__main__":
    main()
