#!/usr/bin/env python3
"""
capability_similarity.py — DR-69: Compute similarity between capability vectors.

Two materials with similar capability profiles are likely substitutes
or analogues. This module computes:

  - Cosine similarity over binary capability vectors
  - Jaccard overlap (intersection / union)
  - Hamming distance (count of differing bits)
  - Dice coefficient (2|A∩B| / (|A|+|B|))

Each metric returns a SimilarityResult with the score and the shared
capabilities (for explainability).

Usage:
    from scripts.capability_similarity import CapabilitySimilarity
    cs = CapabilitySimilarity()
    result = cs.similarity(
        entity_a="bismuth_telluride",
        caps_a={"conducts_electricity", "transfers_heat", "stores_thermal_energy"},
        entity_b="lead_telluride",
        caps_b={"conducts_electricity", "transfers_heat"})
"""
import sys
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Set, Optional, Any, Tuple, Iterable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass
class SimilarityResult:
    """The output of CapabilitySimilarity.similarity()."""
    entity_a: str
    entity_b: str
    caps_a: List[str] = field(default_factory=list)
    caps_b: List[str] = field(default_factory=list)
    cosine: float = 0.0
    jaccard: float = 0.0
    dice: float = 0.0
    hamming: int = 0
    shared: List[str] = field(default_factory=list)
    only_a: List[str] = field(default_factory=list)
    only_b: List[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_a": self.entity_a, "entity_b": self.entity_b,
            "caps_a": self.caps_a, "caps_b": self.caps_b,
            "cosine": self.cosine, "jaccard": self.jaccard,
            "dice": self.dice, "hamming": self.hamming,
            "shared": self.shared, "only_a": self.only_a, "only_b": self.only_b,
            "timestamp": self.timestamp,
        }


@dataclass
class SimilarityMatch:
    """A single match in a search."""
    entity: str
    score: float
    shared: List[str]


class CapabilitySimilarity:
    """DR-69: capability-vector similarity."""

    # ----- public API ---------------------------------------------------
    def similarity(self, entity_a: str, caps_a: Iterable[str],
                   entity_b: str, caps_b: Iterable[str]) -> SimilarityResult:
        """Compute multiple similarity metrics between two capability sets."""
        a = set(caps_a)
        b = set(caps_b)
        shared = a & b
        only_a = a - b
        only_b = b - a
        union = a | b

        # Cosine similarity on binary vectors:
        # cos = |A∩B| / sqrt(|A| * |B|)
        if len(a) > 0 and len(b) > 0:
            cosine = len(shared) / math.sqrt(len(a) * len(b))
        else:
            cosine = 0.0

        # Jaccard = |A∩B| / |A∪B|
        jaccard = len(shared) / len(union) if union else 0.0

        # Dice = 2|A∩B| / (|A|+|B|)
        denom = len(a) + len(b)
        dice = (2.0 * len(shared)) / denom if denom > 0 else 0.0

        # Hamming distance on the union vector
        hamming = len(only_a) + len(only_b)

        return SimilarityResult(
            entity_a=entity_a, entity_b=entity_b,
            caps_a=sorted(a), caps_b=sorted(b),
            cosine=round(cosine, 6),
            jaccard=round(jaccard, 6),
            dice=round(dice, 6),
            hamming=hamming,
            shared=sorted(shared),
            only_a=sorted(only_a),
            only_b=sorted(only_b),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def find_similar(self, query: str, query_caps: Iterable[str],
                     candidates: Dict[str, Iterable[str]],
                     metric: str = "cosine",
                     top_k: int = 5) -> List[SimilarityMatch]:
        """Find the most similar entities to a query.

        Args:
            query: name of the query entity
            query_caps: capabilities of the query
            candidates: dict of {entity: capabilities}
            metric: 'cosine', 'jaccard', or 'dice'
            top_k: number of top matches to return

        Returns:
            List of SimilarityMatch (top_k), sorted by score descending
        """
        results: List[SimilarityMatch] = []
        for ent, caps in candidates.items():
            if ent == query:
                continue
            r = self.similarity(query, query_caps, ent, caps)
            score = {"cosine": r.cosine, "jaccard": r.jaccard,
                     "dice": r.dice}.get(metric, r.cosine)
            results.append(SimilarityMatch(
                entity=ent, score=score, shared=r.shared))
        results.sort(key=lambda m: m.score, reverse=True)
        return results[:top_k]


def main():
    print("=" * 60)
    print("CAPABILITY SIMILARITY (DR-69)")
    print("=" * 60)
    print()

    cs = CapabilitySimilarity()

    # Demo: thermoelectric analogues
    materials = {
        "bismuth_telluride": {"conducts_electricity", "transfers_heat",
                              "stores_thermal_energy"},
        "lead_telluride": {"conducts_electricity", "transfers_heat"},
        "silicon": {"conducts_electricity", "absorbs_light"},
        "graphene": {"conducts_electricity", "transfers_heat", "absorbs_light"},
        "aerogel": {"transfers_heat", "resists_thermal_shock"},
    }

    print("Pairwise: bismuth_telluride vs lead_telluride")
    r = cs.similarity(
        "bismuth_telluride", materials["bismuth_telluride"],
        "lead_telluride", materials["lead_telluride"])
    print(f"  cosine = {r.cosine:.3f}")
    print(f"  jaccard = {r.jaccard:.3f}")
    print(f"  dice = {r.dice:.3f}")
    print(f"  shared = {r.shared}")
    print()

    print("Find similar to bismuth_telluride (cosine, top 3):")
    matches = cs.find_similar("bismuth_telluride",
                              materials["bismuth_telluride"],
                              materials, metric="cosine", top_k=3)
    for m in matches:
        print(f"  {m.entity}: cosine={m.score:.3f} shared={m.shared}")


if __name__ == "__main__":
    main()
