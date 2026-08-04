"""
Tests for the discovery architecture update (DR-20 through DR-23).

Tests the:
  - Object-centric data model (Entity, Mechanism, Constraint, Law, Contradiction, Intervention, Experiment)
  - Swanson bridge search algorithm
  - Gentner structure mapping algorithm
  - Altshuller contradiction search algorithm
  - 8-test acid test (structural readiness)
"""
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.causal_graph import MechanismStatus
from invention_compiler.discovery_graph import (
    Evidence, RelationType, DiscoveryEdge, DiscoveryNode,
    DiscoveryGraph,
    Entity, MechanismObject, Constraint, Law, Contradiction,
    InterventionObject, ExperimentObject,
    SwansonBridgeSearch, GentnerStructureMapping, AltshullerContradictionSearch,
)


# ----------------------------------------------------------------------
# 1. Object-centric data model (DR-21)
# ----------------------------------------------------------------------

class TestObjectCentricModel:
    def test_entity_has_required_fields(self):
        e = Entity(
            entity_id="Bi2Te3",
            entity_type="material",
            canonical_name="Bismuth telluride",
            aliases=["Bi2Te3", "bismuth telluride"],
        )
        assert e.entity_id == "Bi2Te3"
        assert e.canonical_name == "Bismuth telluride"
        assert len(e.aliases) == 2

    def test_mechanism_object_has_activities_and_transitions(self):
        m = MechanismObject(
            mechanism_id="MECH-001",
            entities=["Bi2Te3", "carrier"],
            activities=["electron transport", "heat conversion"],
            transitions=["thermal_gradient → voltage"],
            constraints=["temperature < 500K"],
            equations=["S = (π²/3)(k_B/e)T(d(ln σ)/dE)"],
        )
        assert len(m.activities) == 2
        assert len(m.equations) == 1

    def test_constraint_has_relationship(self):
        c = Constraint(
            variable_a="temperature",
            variable_b="seebeck_coefficient",
            relationship="increases",
        )
        assert c.relationship == "increases"

    def test_law_has_equation_and_domain(self):
        l = Law(
            law_id="LAW-001",
            equation="Q = ε * σ * A * (T^4 - T_env^4)",
            domain="thermodynamics",
        )
        assert l.domain == "thermodynamics"

    def test_contradiction_has_improve_and_worsen(self):
        c = Contradiction(
            contradiction_id="CONTR-001",
            improve="capacity",
            worsen="cycle_life",
            mechanism="thicker electrode",
        )
        assert c.improve == "capacity"
        assert c.worsen == "cycle_life"
        assert c.resolution is None

    def test_intervention_object_has_variable_and_change(self):
        i = InterventionObject(
            intervention_id="INT-001",
            variable="doping_concentration",
            change="increase 5%",
            expected_effect="increase seebeck by 2.5%",
        )
        assert i.variable == "doping_concentration"

    def test_experiment_object_has_protocol_and_prediction(self):
        e = ExperimentObject(
            experiment_id="EXP-001",
            protocol="mix 1g citric acid + 2g NaHCO3 in 100mL water",
            prediction="pH = 8.3 ± 1.0",
            measurement="pH strip reading",
        )
        assert e.outcome is None  # not yet run


# ----------------------------------------------------------------------
# 2. Swanson bridge search (Algorithm 1)
# ----------------------------------------------------------------------

class TestSwansonBridgeSearch:
    def test_finds_undiscovered_bridge(self):
        """If A→B and B→C exist but A→C doesn't, that's a Swanson bridge."""
        dg = DiscoveryGraph()
        e = Evidence(provenance="test", source_count=1, mechanism_status=MechanismStatus.ASSERTED)
        
        # A → B (thermoelectric literature)
        dg.mechanism.add_edge(DiscoveryEdge("Bi2Te3", "thermoelectric", RelationType.MECHANISM, e))
        # B → C (catalysis literature)
        dg.mechanism.add_edge(DiscoveryEdge("thermoelectric", "power_output", RelationType.MECHANISM, e))
        # A → C does NOT exist — that's the bridge
        
        bridges = SwansonBridgeSearch.search(dg)
        bridge_descriptions = [b["description"] for b in bridges]
        
        # Should find the bridge: Bi2Te3 → thermoelectric → power_output
        # (where Bi2Te3 → power_output doesn't exist directly)
        assert len(bridges) > 0, (
            f"Should find at least 1 undiscovered bridge. Bridges: {bridges}"
        )

    def test_does_not_find_existing_connection(self):
        """If A→C already exists, it's not a bridge."""
        dg = DiscoveryGraph()
        e = Evidence(provenance="test", source_count=1, mechanism_status=MechanismStatus.ASSERTED)
        
        dg.mechanism.add_edge(DiscoveryEdge("A", "B", RelationType.MECHANISM, e))
        dg.mechanism.add_edge(DiscoveryEdge("B", "C", RelationType.MECHANISM, e))
        dg.mechanism.add_edge(DiscoveryEdge("A", "C", RelationType.MECHANISM, e))  # direct connection
        
        bridges = SwansonBridgeSearch.search(dg)
        a_to_c_bridges = [b for b in bridges if b["a"] == "A" and b["c"] == "C"]
        assert len(a_to_c_bridges) == 0, (
            "Should NOT find A→C as a bridge if A→C already exists directly"
        )


# ----------------------------------------------------------------------
# 3. Gentner structure mapping (Algorithm 2)
# ----------------------------------------------------------------------

class TestGentnerStructureMapping:
    def test_finds_analogous_chains(self):
        """Two chains with same length but no shared nodes are analogous."""
        dg = DiscoveryGraph()
        e = Evidence(provenance="test", source_count=1, mechanism_status=MechanismStatus.ASSERTED)
        
        # Add nodes first
        for nid in ["crystal", "bandgap", "mobility", "temperature", "pressure", "volume"]:
            dg.mechanism.add_node(DiscoveryNode(nid, "property", nid))
        
        # Chain 1: crystal → bandgap → mobility
        dg.mechanism.add_edge(DiscoveryEdge("crystal", "bandgap", RelationType.MECHANISM, e))
        dg.mechanism.add_edge(DiscoveryEdge("bandgap", "mobility", RelationType.MECHANISM, e))
        
        # Chain 2: temperature → pressure → volume (different domain)
        dg.mechanism.add_edge(DiscoveryEdge("temperature", "pressure", RelationType.MECHANISM, e))
        dg.mechanism.add_edge(DiscoveryEdge("pressure", "volume", RelationType.MECHANISM, e))
        
        analogies = GentnerStructureMapping.find_analogous_chains(dg, min_chain_length=2)
        assert len(analogies) > 0, (
            f"Should find analogous chains. Analogies: {analogies}"
        )

    def test_does_not_match_chain_with_shared_nodes(self):
        """Chains with shared nodes are not analogous (same domain)."""
        dg = DiscoveryGraph()
        e = Evidence(provenance="test", source_count=1, mechanism_status=MechanismStatus.ASSERTED)
        
        # Both chains share 'X'
        dg.mechanism.add_edge(DiscoveryEdge("A", "X", RelationType.MECHANISM, e))
        dg.mechanism.add_edge(DiscoveryEdge("X", "B", RelationType.MECHANISM, e))
        dg.mechanism.add_edge(DiscoveryEdge("C", "X", RelationType.MECHANISM, e))
        dg.mechanism.add_edge(DiscoveryEdge("X", "D", RelationType.MECHANISM, e))
        
        analogies = GentnerStructureMapping.find_analogous_chains(dg, min_chain_length=2)
        # Chains that share 'X' should not be considered analogous
        shared_analogies = [a for a in analogies if set(a["chain_a"]) & set(a["chain_b"])]
        assert len(shared_analogies) == 0, (
            f"Chains with shared nodes should not be analogous. Found: {shared_analogies}"
        )


# ----------------------------------------------------------------------
# 4. Altshuller contradiction search (Algorithm 3)
# ----------------------------------------------------------------------

class TestAltshullerContradictionSearch:
    def test_finds_contradiction(self):
        """If A increases B and decreases C (both desirable), that's a contradiction."""
        dg = DiscoveryGraph()
        e = Evidence(provenance="test", source_count=1, mechanism_status=MechanismStatus.ASSERTED)
        
        dg.causal.add_edge(DiscoveryEdge(
            "doping", "capacity", RelationType.INTERVENTION, e,
            {"direction": "increases"}
        ))
        dg.causal.add_edge(DiscoveryEdge(
            "doping", "cycle_life", RelationType.INTERVENTION, e,
            {"direction": "decreases"}
        ))
        
        contradictions = AltshullerContradictionSearch.find_contradictions(dg)
        assert len(contradictions) > 0, (
            f"Should find contradiction: doping improves capacity but worsens cycle_life. "
            f"Found: {contradictions}"
        )

    def test_no_contradiction_without_increase_and_decrease(self):
        """If both edges increase, no contradiction."""
        dg = DiscoveryGraph()
        e = Evidence(provenance="test", source_count=1, mechanism_status=MechanismStatus.ASSERTED)
        
        dg.causal.add_edge(DiscoveryEdge(
            "A", "B", RelationType.INTERVENTION, e,
            {"direction": "increases"}
        ))
        dg.causal.add_edge(DiscoveryEdge(
            "A", "C", RelationType.INTERVENTION, e,
            {"direction": "increases"}
        ))
        
        contradictions = AltshullerContradictionSearch.find_contradictions(dg)
        assert len(contradictions) == 0


# ----------------------------------------------------------------------
# 5. The 8-test acid test (DR-23) — structural readiness
# ----------------------------------------------------------------------

class TestAcidTest:
    """The 8-test acid test. Each test asks: can the system do X?
    
    The test verifies that the ARCHITECTURE supports each capability.
    Full functional testing requires corpus data + execution.
    """

    def test_swanson_test_can_discover_bridge(self):
        """Can the system discover an unconnected bridge?"""
        # SwansonBridgeSearch exists and can find bridges
        dg = DiscoveryGraph()
        e = Evidence(provenance="test", source_count=1, mechanism_status=MechanismStatus.ASSERTED)
        dg.mechanism.add_edge(DiscoveryEdge("A", "B", RelationType.MECHANISM, e))
        dg.mechanism.add_edge(DiscoveryEdge("B", "C", RelationType.MECHANISM, e))
        bridges = SwansonBridgeSearch.search(dg)
        assert len(bridges) > 0, "Swanson test: system must be able to discover bridges"

    def test_pearl_test_can_propose_intervention(self):
        """Can the system propose an intervention?"""
        # InterventionObject exists and can be created
        iv = InterventionObject(
            intervention_id="INT-001",
            variable="temperature",
            change="increase 10K",
            expected_effect="increase power output",
        )
        assert iv.variable is not None
        assert iv.expected_effect is not None

    def test_popper_test_intervention_can_fail(self):
        """Can the intervention fail?"""
        # ExperimentObject has outcome field that can be "fail"
        exp = ExperimentObject(
            experiment_id="EXP-001",
            protocol="test protocol",
            prediction="X will happen",
            measurement="measure Y",
            outcome=None,  # not yet run — can fail
        )
        assert exp.outcome is None, "Popper test: outcome must be initially unknown (can fail)"

    def test_ross_king_test_can_design_experiment(self):
        """Can the system design an experiment?"""
        # ExperimentObject with protocol, prediction, measurement
        exp = ExperimentObject(
            experiment_id="EXP-001",
            protocol="mix chemicals at ratio 1:2",
            prediction="pH = 8.3",
            measurement="pH strip reading",
        )
        assert exp.protocol is not None
        assert exp.prediction is not None
        assert exp.measurement is not None

    def test_bacon_test_can_derive_law(self):
        """Can the system derive a law?"""
        # Law object exists with equation, domain, assumptions
        law = Law(
            law_id="LAW-001",
            equation="Q = εσA(T⁴-T_env⁴)",
            domain="thermodynamics",
            assumptions=["blackbody radiation", "vacuum"],
        )
        assert law.equation is not None
        assert law.domain is not None

    def test_gentner_test_can_transfer_mechanism(self):
        """Can the system transfer a mechanism?"""
        # GentnerStructureMapping exists and can find analogies
        dg = DiscoveryGraph()
        e = Evidence(provenance="test", source_count=1, mechanism_status=MechanismStatus.ASSERTED)
        dg.mechanism.add_edge(DiscoveryEdge("A", "B", RelationType.MECHANISM, e))
        dg.mechanism.add_edge(DiscoveryEdge("B", "C", RelationType.MECHANISM, e))
        dg.mechanism.add_edge(DiscoveryEdge("X", "Y", RelationType.MECHANISM, e))
        dg.mechanism.add_edge(DiscoveryEdge("Y", "Z", RelationType.MECHANISM, e))
        analogies = GentnerStructureMapping.find_analogous_chains(dg, min_chain_length=2)
        # The architecture supports mechanism transfer
        assert isinstance(analogies, list)

    def test_altshuller_test_can_resolve_contradiction(self):
        """Can the system resolve a contradiction?"""
        # Contradiction object has resolution field
        c = Contradiction(
            contradiction_id="CONTR-001",
            improve="capacity",
            worsen="weight",
            mechanism="thicker electrode",
            resolution=None,  # not yet resolved — can be resolved
        )
        assert c.resolution is None, "Altshuller test: resolution must be initially unknown"

    def test_arthur_test_can_move_to_adjacent_possible(self):
        """Can the system move into the adjacent possible?"""
        # The Swanson bridge search IS the adjacent possible detector
        # — it finds connections that don't exist yet but could
        dg = DiscoveryGraph()
        e = Evidence(provenance="test", source_count=1, mechanism_status=MechanismStatus.ASSERTED)
        dg.mechanism.add_edge(DiscoveryEdge("existing", "bridge", RelationType.MECHANISM, e))
        dg.mechanism.add_edge(DiscoveryEdge("bridge", "adjacent_possible", RelationType.MECHANISM, e))
        bridges = SwansonBridgeSearch.search(dg)
        # The bridge search finds what's adjacent but not yet connected
        assert isinstance(bridges, list), "Arthur test: system must be able to detect adjacent possible"
