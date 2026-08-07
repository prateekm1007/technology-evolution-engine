#!/usr/bin/env python3
"""
capability_graph.py — Capability graph for invention (Stage 0.5).

Capabilities are intermediate objects between discovery and invention.
They represent what a material/system CAN DO, not what it IS.

This module:
1. Defines the Capability and CapabilityEdge dataclasses
2. Provides the CapabilityGraph class
3. Derives capabilities from extracted relations (discovery graph → capability graph)

Usage:
    from scripts.capability_graph import CapabilityGraph, Capability
    cg = CapabilityGraph()
    cg.from_relations([("graphene", "conducts", "electricity"), ...])
    caps = cg.get_capabilities("graphene")  # → [conducts_electricity, ...]
"""
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass
class Capability:
    """A capability that an entity possesses."""
    capability_id: str
    name: str            # e.g., "conducts_electricity"
    category: str        # electrical, thermal, mechanical, chemical, optical
    direction: str       # "enable" or "prevent"
    measured_by: str     # how to verify
    units: str           # SI units
    typical_range: Tuple[float, float]  # (min, max)


@dataclass
class CapabilityEdge:
    """An edge in the capability graph."""
    source: str          # entity that HAS the capability
    capability: str      # capability name
    target: str          # what the capability acts ON (optional, "")
    confidence: float    # 0-1
    provenance: str      # source


# Capability derivation rules: map (verb, object_keyword) → Capability
CAPABILITY_RULES = [
    # Electrical
    {"verb_pattern": r"conduct|conducts", "object_keyword": "electric|electrical|current",
     "capability": "conducts_electricity", "category": "electrical", "direction": "enable",
     "measured_by": "four_point_probe", "units": "S/m", "range": (1e-8, 1e8)},
    {"verb_pattern": r"store|stores|accumulate", "object_keyword": "charge|energy|capacit",
     "capability": "stores_charge", "category": "electrical", "direction": "enable",
     "measured_by": "cyclic_voltammetry", "units": "F/g", "range": (0.1, 500)},
    {"verb_pattern": r"generate|generates|produce|produces", "object_keyword": "voltage|current|power|electric",
     "capability": "generates_voltage", "category": "electrical", "direction": "enable",
     "measured_by": "open_circuit_voltage", "units": "V", "range": (0.01, 100)},

    # Thermal
    {"verb_pattern": r"transfer|transfers|conduct|conducts", "object_keyword": "heat|thermal",
     "capability": "transfers_heat", "category": "thermal", "direction": "enable",
     "measured_by": "laser_flash_analysis", "units": "W/(m·K)", "range": (0.01, 1000)},
    {"verb_pattern": r"absorb|absorbs|store|stores", "object_keyword": "heat|thermal|latent",
     "capability": "stores_thermal_energy", "category": "thermal", "direction": "enable",
     "measured_by": "differential_scanning_calorimetry", "units": "J/g", "range": (10, 5000)},
    {"verb_pattern": r"resist|resists|withstand|survives", "object_keyword": "thermal|temperature|heat|shock|cycling",
     "capability": "resists_thermal_shock", "category": "thermal", "direction": "enable",
     "measured_by": "thermal_cycling_test", "units": "cycles", "range": (10, 10000)},
    {"verb_pattern": r"emit|emits|radiat", "object_keyword": "heat|thermal|infrared",
     "capability": "emits_thermal_radiation", "category": "thermal", "direction": "enable",
     "measured_by": "emissivity_measurement", "units": "emissivity", "range": (0.01, 1.0)},

    # Mechanical
    {"verb_pattern": r"bear|bears|support|withstand", "object_keyword": "load|stress|pressure|force",
     "capability": "bears_load", "category": "mechanical", "direction": "enable",
     "measured_by": "tensile_test", "units": "MPa", "range": (1, 10000)},
    {"verb_pattern": r"resist|resists|prevent|prevents", "object_keyword": "deform|wear|fatigue|fracture|crack",
     "capability": "resists_deformation", "category": "mechanical", "direction": "enable",
     "measured_by": "hardness_test", "units": "GPa", "range": (0.1, 100)},
    {"verb_pattern": r"damp|damps|absorb|absorbs|dissipat", "object_keyword": "vibrat|oscillat|mechanical",
     "capability": "damps_vibration", "category": "mechanical", "direction": "enable",
     "measured_by": "dynamic_mechanical_analysis", "units": "tan(δ)", "range": (0.01, 2.0)},

    # Chemical
    {"verb_pattern": r"resist|resists|prevent|prevents|inhibit", "object_keyword": "corros|oxid|degrad|rust",
     "capability": "resists_corrosion", "category": "chemical", "direction": "enable",
     "measured_by": "salt_spray_test", "units": "mm/year", "range": (0.001, 10)},
    {"verb_pattern": r"catalyz|accelerat|promot", "object_keyword": "reaction|oxid|reduc|split",
     "capability": "catalyzes_reaction", "category": "chemical", "direction": "enable",
     "measured_by": "overpotential_measurement", "units": "V", "range": (0.01, 2.0)},
    {"verb_pattern": r"absorb|absorbs|capture|adsorb", "object_keyword": "gas|CO2|hydrogen|methane",
     "capability": "absorbs_gas", "category": "chemical", "direction": "enable",
     "measured_by": "BET_surface_area", "units": "mmol/g", "range": (0.1, 50)},

    # Optical
    {"verb_pattern": r"absorb|absorbs", "object_keyword": "light|photon|solar|UV|visible|infrared",
     "capability": "absorbs_light", "category": "optical", "direction": "enable",
     "measured_by": "UV_vis_spectroscopy", "units": "absorbance", "range": (0.01, 3.0)},
    {"verb_pattern": r"emit|emits", "object_keyword": "light|photon|luminesc|fluoresc",
     "capability": "emits_light", "category": "optical", "direction": "enable",
     "measured_by": "photoluminescence_spectroscopy", "units": "nm", "range": (200, 2000)},
    {"verb_pattern": r"reflect|reflects", "object_keyword": "light|solar|radiat",
     "capability": "reflects_light", "category": "optical", "direction": "enable",
     "measured_by": "reflectance_spectroscopy", "units": "reflectance", "range": (0.01, 1.0)},
]


class CapabilityGraph:
    """A graph of capabilities derived from the discovery graph.

    Turns entities and relations into capabilities:
    - "graphene --conducts--> electricity" → capability(graphene, conducts_electricity)
    - "PCM --absorbs--> heat" → capability(PCM, stores_thermal_energy)
    """

    def __init__(self):
        self.edges: List[CapabilityEdge] = []
        self.capabilities_by_entity: Dict[str, List[CapabilityEdge]] = defaultdict(list)
        self.all_capability_names: Set[str] = set()

    def from_relations(self, relations: List[Tuple[str, str, str]],
                       provenance: str = "discovery_graph") -> int:
        """Derive capabilities from extracted relations.

        Args:
            relations: list of (subject, verb, object) tuples
            provenance: source of the relations

        Returns:
            number of capabilities derived
        """
        import re
        count = 0
        for subj, verb, obj in relations:
            subj_lower = subj.lower().strip()
            verb_lower = verb.lower().strip()
            obj_lower = obj.lower().strip()

            for rule in CAPABILITY_RULES:
                verb_match = re.search(rule["verb_pattern"], verb_lower)
                # Object match: check if ANY keyword from the pattern appears in the object
                keywords = rule["object_keyword"].split("|")
                obj_match = any(kw in obj_lower for kw in keywords)

                if verb_match and obj_match:
                    cap = Capability(
                        capability_id=f"CAP-{len(self.edges):04d}",
                        name=rule["capability"],
                        category=rule["category"],
                        direction=rule["direction"],
                        measured_by=rule["measured_by"],
                        units=rule["units"],
                        typical_range=rule["range"],
                    )
                    edge = CapabilityEdge(
                        source=subj_lower,
                        capability=rule["capability"],
                        target=obj_lower,
                        confidence=0.75,
                        provenance=provenance,
                    )
                    self.edges.append(edge)
                    self.capabilities_by_entity[subj_lower].append(edge)
                    self.all_capability_names.add(rule["capability"])
                    count += 1
                    break  # one capability per relation

        return count

    def from_text(self, text: str, pipeline=None) -> int:
        """Extract capabilities from text using the NLP pipeline.

        Args:
            text: source text
            pipeline: NLPPipeline instance (optional, will create if needed)

        Returns:
            number of capabilities derived
        """
        if pipeline is None:
            from scripts.nlp_pipeline import NLPPipeline
            pipeline = NLPPipeline()

        entities = pipeline.extract_entities(text)
        relations = pipeline.extract_relations(text, entities)
        rel_tuples = [(r.subject.text, r.relation, r.obj.text) for r in relations]
        return self.from_relations(rel_tuples, provenance="nlp_extraction")

    def get_capabilities(self, entity: str) -> List[CapabilityEdge]:
        """Get all capabilities for an entity."""
        return self.capabilities_by_entity.get(entity.lower().strip(), [])

    def get_entities_with_capability(self, capability_name: str) -> List[str]:
        """Get all entities that have a specific capability."""
        return [e.source for e in self.edges if e.capability == capability_name]

    def get_capability_categories(self) -> Set[str]:
        """Get all capability categories present."""
        return set(e.capability.split("_")[0] for e in self.edges)  # simplified

    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return {
            "edges": [
                {"source": e.source, "capability": e.capability, "target": e.target,
                 "confidence": e.confidence, "provenance": e.provenance}
                for e in self.edges
            ],
            "n_capabilities": len(self.edges),
            "n_entities": len(self.capabilities_by_entity),
            "capability_names": sorted(self.all_capability_names),
        }


def main():
    """Demo: capability graph from sample text."""
    print("=" * 60)
    print("CAPABILITY GRAPH (Stage 0.5)")
    print("=" * 60)
    print()

    test_relations = [
        ("graphene", "conducts", "electricity"),
        ("PCM", "absorbs", "heat"),
        ("TiO2 coating", "prevents", "corrosion"),
        ("bismuth telluride", "generates", "voltage"),
        ("aerogel", "prevents", "heat transfer"),
        ("Pd catalyst", "catalyzes", "reaction"),
        ("solar cell", "absorbs", "light"),
        ("LED", "emits", "light"),
    ]

    cg = CapabilityGraph()
    n = cg.from_relations(test_relations)
    print(f"Derived {n} capabilities from {len(test_relations)} relations:")
    print()
    for edge in cg.edges:
        print(f"  {edge.source} → {edge.capability} (target: {edge.target})")
    print()
    print(f"Entities with capabilities: {len(cg.capabilities_by_entity)}")
    print(f"Distinct capabilities: {len(cg.all_capability_names)}")
    print(f"Capability names: {sorted(cg.all_capability_names)}")


if __name__ == "__main__":
    main()
