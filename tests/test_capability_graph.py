"""Tests for capability_graph.py — Stage 0.5."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.capability_graph import CapabilityGraph, Capability, CapabilityEdge


def test_capability_graph_from_relations():
    """Capabilities are derived from relations."""
    cg = CapabilityGraph()
    n = cg.from_relations([
        ("graphene", "conducts", "electricity"),
        ("PCM", "absorbs", "heat"),
        ("TiO2", "prevents", "corrosion"),
    ])
    assert n == 3
    assert len(cg.edges) == 3


def test_get_capabilities_for_entity():
    """Get capabilities for a specific entity."""
    cg = CapabilityGraph()
    cg.from_relations([
        ("graphene", "conducts", "electricity"),
        ("graphene", "absorbs", "light"),
    ])
    caps = cg.get_capabilities("graphene")
    assert len(caps) == 2
    assert any(c.capability == "conducts_electricity" for c in caps)
    assert any(c.capability == "absorbs_light" for c in caps)


def test_get_entities_with_capability():
    """Find all entities with a specific capability."""
    cg = CapabilityGraph()
    cg.from_relations([
        ("graphene", "conducts", "electricity"),
        ("copper", "conducts", "electricity"),
    ])
    entities = cg.get_entities_with_capability("conducts_electricity")
    assert "graphene" in entities
    assert "copper" in entities


def test_capability_categories():
    """Capabilities span multiple categories."""
    cg = CapabilityGraph()
    cg.from_relations([
        ("graphene", "conducts", "electricity"),
        ("PCM", "absorbs", "heat"),
        ("TiO2", "prevents", "corrosion"),
        ("LED", "emits", "light"),
    ])
    # Should have electrical, thermal, chemical, optical
    categories = set()
    for edge in cg.edges:
        for rule in cg._get_rules() if hasattr(cg, '_get_rules') else []:
            pass  # simplified
    # Just verify we have multiple categories
    cap_names = [e.capability for e in cg.edges]
    assert "conducts_electricity" in cap_names  # electrical
    assert "stores_thermal_energy" in cap_names  # thermal
    assert "resists_corrosion" in cap_names  # chemical
    assert "emits_light" in cap_names  # optical


def test_capability_graph_serializable():
    """Capability graph can be serialized to dict."""
    cg = CapabilityGraph()
    cg.from_relations([("graphene", "conducts", "electricity")])
    d = cg.to_dict()
    assert d["n_capabilities"] == 1
    assert len(d["edges"]) == 1
    assert "conducts_electricity" in d["capability_names"]


def test_thermoelectric_domain_compiles():
    """Thermoelectric domain compiles into capability form."""
    cg = CapabilityGraph()
    n = cg.from_relations([
        ("bismuth_telluride", "generates", "voltage"),
        ("bismuth_telluride", "conducts", "heat"),
        ("bismuth_telluride", "conducts", "electricity"),
        ("phonon_scattering", "reduces", "thermal conductivity"),
    ], provenance="thermoelectric_corpus")
    assert n >= 2  # at least generates_voltage + conducts_electricity
    caps = cg.get_capabilities("bismuth_telluride")
    assert len(caps) >= 1
    # Should have generates_voltage
    cap_names = [c.capability for c in caps]
    assert "generates_voltage" in cap_names


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
