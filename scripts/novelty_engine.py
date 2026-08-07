#!/usr/bin/env python3
"""
novelty_engine.py — Stage V: Configuration-level novelty check.

Novelty is checked at the CONFIGURATION level, not the prose level.

The core invariant (see docs/ARTIFACT_SCHEMA.md):

    Two Configurations with the same components, structure, and
    parameters produce the same `config_hash`, regardless of wording,
    generator seed, or operator chain that produced them.

Consequences:

  - Same configuration, different wording → SAME hash → NOT novel.
  - Same configuration, different operator chain → SAME hash → NOT novel.
  - Same configuration, different generator seed → SAME hash → NOT novel.
  - New arrangement of known parts → DIFFERENT hash → NOVEL.
  - Novelty is INDEPENDENT of retrieval phrasing — the spec_objective
    is excluded from the hash.

The engine maintains a registry of known config_hashes (a set). A new
Configuration is novel iff its config_hash is not in the registry.

Usage:
    from scripts.novelty_engine import NoveltyEngine
    engine = NoveltyEngine()
    result = engine.check(new_config)
    # result.is_novel == True/False
    # result.known_match == config_hash if not novel
    engine.register(new_config)  # add to registry
"""
import sys
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Set, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Import the Configuration dataclass from Stage II
from scripts.artifact_generator import Configuration, Component


@dataclass
class NoveltyReport:
    """The output of NoveltyEngine.check()."""
    config_id: str
    config_hash: str
    is_novel: bool
    known_match: Optional[str] = None      # the matching config_id (if not novel)
    known_match_hash: Optional[str] = None
    registry_size: int = 0
    nearest_neighbor_hash: Optional[str] = None  # if a "fuzzy" near-match exists
    nearest_neighbor_distance: int = 0    # Hamming distance in hex chars
    timestamp: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class NoveltyEngine:
    """Stage V: configuration-level novelty checking.

    The engine MUST have a `run()` method because the INVENTION_CONSTITUTION
    naming rule (tests/test_invention_naming.py) requires any class
    named "*Engine" to have generate() or run().

    Novelty is determined by the canonical config_hash, which is the
    SHA-256 of the canonical JSON serialization of the configuration's
    structure, components (sorted, with parameters sorted and rounded),
    and global parameters (sorted, rounded).

    The hash is INVARIANT under:
      - rewording of spec_objective
      - changes to config_id
      - changes to design_operator_chain
      - changes to provenance (timestamps, seeds)
      - changes to source_capabilities

    The hash CHANGES under:
      - different materials in components
      - different parameter values
      - different structure (monolithic vs layered_3 vs segmented_4)
      - different number of components
      - different roles
    """

    HASH_PREFIX_LEN = 16

    def __init__(self, registry: Optional[Set[str]] = None,
                 known_configs: Optional[List[Configuration]] = None):
        """Initialize the engine.

        Args:
            registry: optional set of known config_hashes
            known_configs: optional list of known Configurations to seed the registry
        """
        self._registry: Set[str] = set(registry) if registry else set()
        self._hash_to_config: Dict[str, str] = {}  # hash → config_id
        if known_configs:
            for c in known_configs:
                self.register(c)

    # ----- public API ---------------------------------------------------
    def check(self, config: Configuration) -> NoveltyReport:
        """Check whether a Configuration is novel.

        Args:
            config: a Configuration (must have a non-empty config_hash,
                    or one will be computed)

        Returns:
            NoveltyReport with is_novel, known_match, etc.
        """
        h = config.config_hash or config.compute_hash()
        is_novel = h not in self._registry
        known_id = self._hash_to_config.get(h) if not is_novel else None

        # Nearest neighbor in the registry (Hamming distance on hex chars)
        nearest, dist = self._nearest_neighbor(h)

        return NoveltyReport(
            config_id=config.config_id,
            config_hash=h,
            is_novel=is_novel,
            known_match=known_id,
            known_match_hash=h if not is_novel else None,
            registry_size=len(self._registry),
            nearest_neighbor_hash=nearest,
            nearest_neighbor_distance=dist,
            timestamp=datetime.now(timezone.utc).isoformat(),
            provenance={
                "engine": "NoveltyEngine",
                "stage": "V",
                "method": "config_hash exact match",
                "fuzzy_method": "Hamming distance on hex",
            },
        )

    def register(self, config: Configuration) -> None:
        """Add a Configuration to the registry of known configs."""
        h = config.config_hash or config.compute_hash()
        self._registry.add(h)
        self._hash_to_config[h] = config.config_id

    def register_hash(self, config_hash: str, config_id: str = "unknown") -> None:
        """Register a config_hash directly."""
        self._registry.add(config_hash)
        self._hash_to_config[config_hash] = config_id

    def is_novel(self, config: Configuration) -> bool:
        """Convenience: just return the boolean."""
        return self.check(config).is_novel

    def run(self, configs: List[Configuration],
            register_novel: bool = True) -> List[NoveltyReport]:
        """Check novelty of a batch of Configurations.

        This is the 'generate / run' method required by the Invention
        Constitution naming rule. It runs novelty checking over a batch
        and (optionally) registers novel ones.

        Args:
            configs: list of Configurations to check
            register_novel: if True, novel configs are added to the registry

        Returns:
            list of NoveltyReport (one per config), in input order
        """
        reports: List[NoveltyReport] = []
        for c in configs:
            r = self.check(c)
            if not r.is_novel:
                # already known — skip
                pass
            elif register_novel:
                self.register(c)
            reports.append(r)
        return reports

    def generate(self, configs: List[Configuration]) -> List[NoveltyReport]:
        """Alias for run() — satisfies the 'generate' naming convention too."""
        return self.run(configs, register_novel=False)

    # ----- registry accessors ------------------------------------------
    @property
    def registry(self) -> Set[str]:
        """Return the set of known config_hashes."""
        return set(self._registry)

    def registry_size(self) -> int:
        return len(self._registry)

    def reset(self) -> None:
        """Clear the registry (useful for tests)."""
        self._registry = set()
        self._hash_to_config = {}

    # ----- internals ----------------------------------------------------
    def _nearest_neighbor(self, h: str) -> Tuple[Optional[str], int]:
        """Find the nearest neighbor in the registry by Hamming distance.

        Args:
            h: a config_hash (16 hex chars)

        Returns:
            (nearest_hash, distance). If registry is empty, returns (None, 0).
        """
        if not self._registry:
            return None, 0
        best_h = None
        best_d = len(h) + 1
        for known in self._registry:
            # Hamming distance on hex chars
            d = sum(1 for a, b in zip(h, known) if a != b)
            # If lengths differ, count the difference
            d += abs(len(h) - len(known))
            if d < best_d:
                best_d = d
                best_h = known
        return best_h, best_d


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
def main():
    """Demo: novelty checking on a batch of generated configurations."""
    print("=" * 60)
    print("NOVELTY ENGINE (Stage V)")
    print("=" * 60)
    print()

    from scripts.artifact_generator import ArtifactGenerator, MATERIAL_PARAMS
    from scripts.specification import SpecificationEngine
    from scripts.capability_graph import CapabilityGraph

    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([
        ("bismuth telluride", "generates", "voltage"),
        ("lead telluride", "generates", "voltage"),
    ])

    # Generate a batch and check novelty
    gen = ArtifactGenerator(seed=42)
    batch = gen.generate(spec, cg, n=8)
    engine = NoveltyEngine()

    print("Batch 1 (fresh registry):")
    reports = engine.run(batch, register_novel=True)
    for r in reports:
        flag = "NOVEL" if r.is_novel else "KNOWN"
        print(f"  {r.config_id}  hash={r.config_hash}  {flag}"
              f"  registry_size={r.registry_size}")

    print()
    print("Batch 2 (same generator, same seed → same configs):")
    batch2 = ArtifactGenerator(seed=42).generate(spec, cg, n=8)
    reports2 = engine.run(batch2, register_novel=False)
    n_novel = sum(1 for r in reports2 if r.is_novel)
    n_known = sum(1 for r in reports2 if not r.is_novel)
    print(f"  novel={n_novel}, known={n_known}")
    assert n_known == 8, "same seed should reproduce same hashes → all known"
    print("  PASS: same seed produces same hashes → all KNOWN")

    print()
    print("Batch 3 (different seed):")
    batch3 = ArtifactGenerator(seed=99).generate(spec, cg, n=8)
    reports3 = engine.run(batch3, register_novel=True)
    n_novel = sum(1 for r in reports3 if r.is_novel)
    print(f"  novel={n_novel} / {len(reports3)}")

    print()
    print("Wording-independence test:")
    # Two configs identical except for spec_objective → same hash
    from scripts.artifact_generator import Component
    c1 = Configuration(
        config_id="W1", spec_objective="improve TE efficiency of Bi2Te3",
        domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    c2 = Configuration(
        config_id="W2",
        spec_objective="boost ZT of bismuth telluride — different wording",
        domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init", "substitute", "amplify"],  # different chain!
    )
    c1.config_hash = c1.compute_hash()
    c2.config_hash = c2.compute_hash()
    print(f"  c1 hash = {c1.config_hash}  (objective: '{c1.spec_objective}')")
    print(f"  c2 hash = {c2.config_hash}  (objective: '{c2.spec_objective}')")
    print(f"  equal?  {c1.config_hash == c2.config_hash}")
    assert c1.config_hash == c2.config_hash, (
        "different wording / different chain must NOT change the hash")
    print("  PASS: same configuration → same hash, regardless of wording")


if __name__ == "__main__":
    main()
