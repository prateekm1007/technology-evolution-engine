"""Tests for DR-69: capability graph evolution."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.capability_reasoner import (
    CapabilityReasoner, InferenceRule, InferredCapability, ReasoningResult,
)
from scripts.capability_composer import (
    CapabilityComposer, CompositionRule, ComposedCapability, CompositionResult,
)
from scripts.capability_similarity import (
    CapabilitySimilarity, SimilarityResult, SimilarityMatch,
)
from scripts.capability_constraints import (
    CapabilityConstraints, CapabilityConstraint, ConstraintDerivationResult,
)


# ---------------------------------------------------------------------------
# DR-69.1: capability_reasoner.py
# ---------------------------------------------------------------------------
def test_reasoner_infers_seebeck_chain():
    """conducts_electricity + transfers_heat → can_generate_current."""
    cr = CapabilityReasoner()
    result = cr.infer(["conducts_electricity", "transfers_heat"])
    names = [ic.name for ic in result.inferred]
    assert "can_generate_current" in names


def test_reasoner_chains_to_thermoelectric_generator():
    """Multi-hop inference: conducts + transfers + stores_thermal → TE generator."""
    cr = CapabilityReasoner()
    result = cr.infer([
        "conducts_electricity", "transfers_heat", "stores_thermal_energy",
        "resists_corrosion",
    ])
    closure = set(result.closure)
    # Should chain: can_generate_current → thermoelectric_candidate →
    # thermoelectric_generator; stable_electrode → energy_harvesting_device
    assert "can_generate_current" in closure
    assert "thermoelectric_candidate" in closure
    assert "stable_electrode" in closure
    assert "thermoelectric_generator" in closure


def test_reasoner_no_inference_when_missing_premise():
    """A single capability that matches no rule yields no inference."""
    cr = CapabilityReasoner()
    result = cr.infer(["damps_vibration"])
    assert result.inferred == []
    assert result.closure == ["damps_vibration"]


def test_reasoner_terminates_on_fixpoint():
    """The reasoner stops at a fixpoint (no infinite loop)."""
    cr = CapabilityReasoner(max_iterations=20)
    result = cr.infer(["conducts_electricity", "transfers_heat",
                       "stores_thermal_energy"])
    assert result.n_iterations <= 20
    # Re-running should produce the same closure
    result2 = cr.infer(["conducts_electricity", "transfers_heat",
                        "stores_thermal_energy"])
    assert result.closure == result2.closure


def test_reasoner_explain_returns_mechanism():
    """explain() returns the physics mechanism for an inferred capability."""
    cr = CapabilityReasoner()
    result = cr.infer(["conducts_electricity", "transfers_heat"])
    expl = cr.explain("can_generate_current", result)
    assert expl is not None
    assert "Seebeck" in expl or "seebeck" in expl.lower() or "temperature" in expl.lower()


def test_reasoner_custom_rule_works():
    """User-supplied rules are honored."""
    cr = CapabilityReasoner(rules=[])
    cr.add_rule(InferenceRule(
        rule_id="X-001",
        premises=["a", "b"],
        conclusion="c",
        mechanism="custom rule",
    ))
    result = cr.infer(["a", "b"])
    assert "c" in result.closure


def test_reasoner_result_serializable():
    import json
    cr = CapabilityReasoner()
    result = cr.infer(["conducts_electricity", "transfers_heat"])
    json.dumps(result.to_dict())


# ---------------------------------------------------------------------------
# DR-69.2: capability_composer.py
# ---------------------------------------------------------------------------
def test_composer_combines_conductor_and_heat_transfer():
    """conducts_electricity (A) + transfers_heat (B) → heterojunction_thermoelectric."""
    cc = CapabilityComposer()
    r = cc.compose(
        material_a="bismuth_telluride", caps_a=["conducts_electricity"],
        material_b="graphene", caps_b=["transfers_heat"])
    names = [c.capability for c in r.composed]
    assert "heterojunction_thermoelectric" in names


def test_composer_is_commutative_when_unordered():
    """Swapping A and B should still match an unordered rule."""
    cc = CapabilityComposer()
    r1 = cc.compose(
        material_a="X", caps_a=["conducts_electricity"],
        material_b="Y", caps_b=["transfers_heat"])
    r2 = cc.compose(
        material_a="Y", caps_a=["transfers_heat"],
        material_b="X", caps_b=["conducts_electricity"])
    n1 = {c.capability for c in r1.composed}
    n2 = {c.capability for c in r2.composed}
    assert "heterojunction_thermoelectric" in n1
    assert "heterojunction_thermoelectric" in n2


def test_composer_returns_empty_when_no_rule_matches():
    """No composition possible when caps don't match any rule."""
    cc = CapabilityComposer()
    r = cc.compose(
        material_a="rubber", caps_a=["damps_vibration"],
        material_b="glass", caps_b=["reflects_light"])
    assert r.composed == []


def test_composer_multiple_rules_fire():
    """A material with many capabilities triggers multiple rules."""
    cc = CapabilityComposer()
    r = cc.compose(
        material_a="tio2", caps_a=["catalyzes_reaction", "absorbs_light"],
        material_b="carbon", caps_b=["conducts_electricity"])
    # Should fire: bifunctional_electrocatalyst (catalyst + conductor)
    # and photo_supercapacitor (light + charge) — but carbon doesn't store
    # charge, so only the catalyst one fires.
    names = {c.capability for c in r.composed}
    assert "bifunctional_electrocatalyst" in names


def test_composer_result_serializable():
    import json
    cc = CapabilityComposer()
    r = cc.compose(
        material_a="A", caps_a=["conducts_electricity"],
        material_b="B", caps_b=["transfers_heat"])
    json.dumps(r.to_dict())


# ---------------------------------------------------------------------------
# DR-69.3: capability_similarity.py
# ---------------------------------------------------------------------------
def test_similarity_identical_sets_score_one():
    """Two identical capability sets have cosine = jaccard = 1.0."""
    cs = CapabilitySimilarity()
    r = cs.similarity(
        "A", {"conducts_electricity", "transfers_heat"},
        "B", {"conducts_electricity", "transfers_heat"})
    assert abs(r.cosine - 1.0) < 1e-9
    assert abs(r.jaccard - 1.0) < 1e-9
    assert abs(r.dice - 1.0) < 1e-9
    assert r.hamming == 0


def test_similarity_disjoint_sets_score_zero():
    """Disjoint capability sets have cosine = jaccard = 0."""
    cs = CapabilitySimilarity()
    r = cs.similarity(
        "A", {"conducts_electricity"},
        "B", {"absorbs_light"})
    assert r.cosine == 0.0
    assert r.jaccard == 0.0
    assert r.dice == 0.0
    assert r.shared == []


def test_similarity_partial_overlap():
    """Partial overlap produces 0 < score < 1."""
    cs = CapabilitySimilarity()
    r = cs.similarity(
        "A", {"conducts_electricity", "transfers_heat"},
        "B", {"conducts_electricity", "absorbs_light"})
    # 1 shared, 2 in A, 2 in B → cosine = 1/sqrt(4) = 0.5
    assert abs(r.cosine - 0.5) < 1e-6
    # Jaccard = 1/3
    assert abs(r.jaccard - 1.0/3.0) < 1e-6
    # shared = {"conducts_electricity"}
    assert r.shared == ["conducts_electricity"]
    assert "transfers_heat" in r.only_a
    assert "absorbs_light" in r.only_b


def test_similarity_find_similar_returns_sorted():
    """find_similar returns top-k matches sorted by score."""
    cs = CapabilitySimilarity()
    candidates = {
        "B": {"conducts_electricity", "transfers_heat"},
        "C": {"absorbs_light"},
        "D": {"conducts_electricity"},
    }
    matches = cs.find_similar(
        "A", {"conducts_electricity"}, candidates,
        metric="cosine", top_k=2)
    assert len(matches) == 2
    assert matches[0].score >= matches[1].score
    # B and D both share conducts_electricity with A
    assert matches[0].entity in {"B", "D"}


def test_similarity_empty_sets_score_zero():
    """Empty capability sets produce zero similarity."""
    cs = CapabilitySimilarity()
    r = cs.similarity("A", set(), "B", set())
    assert r.cosine == 0.0
    assert r.jaccard == 0.0


def test_similarity_result_serializable():
    import json
    cs = CapabilitySimilarity()
    r = cs.similarity("A", {"c1"}, "B", {"c1", "c2"})
    json.dumps(r.to_dict())


# ---------------------------------------------------------------------------
# DR-69.4: capability_constraints.py
# ---------------------------------------------------------------------------
def test_constraints_derive_for_conductor():
    """conducts_electricity → electrical_conductivity > 100 S/m."""
    cc = CapabilityConstraints()
    result = cc.derive(["conducts_electricity"])
    params = [(c.parameter, c.operator, c.threshold) for c in result.constraints]
    assert ("electrical_conductivity", ">", 1.0e2) in params
    assert ("resistivity", "<", 1.0e-2) in params


def test_constraints_derive_for_multiple_caps():
    """Multiple capabilities produce multiple constraints."""
    cc = CapabilityConstraints()
    result = cc.derive(["conducts_electricity", "transfers_heat",
                        "emits_thermal_radiation"])
    assert result.n_constraints >= 3
    params = {c.parameter for c in result.constraints}
    assert "electrical_conductivity" in params
    assert "thermal_conductivity" in params
    assert "emissivity" in params


def test_constraints_check_candidate_pass():
    """A candidate satisfying all constraints passes."""
    cc = CapabilityConstraints()
    check = cc.check_candidate(
        ["conducts_electricity", "transfers_heat"],
        {"electrical_conductivity": 1.0e5,
         "thermal_conductivity": 1.5})
    assert check["pass"] is True
    assert check["violations"] == []


def test_constraints_check_candidate_fail():
    """A candidate violating a constraint fails with an explicit violation."""
    cc = CapabilityConstraints()
    check = cc.check_candidate(
        ["conducts_electricity"],
        {"electrical_conductivity": 1.0e-3})
    assert check["pass"] is False
    assert len(check["violations"]) >= 1
    v = check["violations"][0]
    assert v["parameter"] == "electrical_conductivity"
    assert v["value"] == 1.0e-3


def test_constraints_missing_parameter_is_not_violation():
    """A missing parameter is a soft skip, not a violation."""
    cc = CapabilityConstraints()
    check = cc.check_candidate(
        ["conducts_electricity"],
        {})  # no parameters at all
    # No violation, but no check either
    assert check["pass"] is True
    assert check["n_checked"] == 0


def test_constraints_custom_constraint():
    """User can add a custom constraint."""
    cc = CapabilityConstraints()
    cc.add_constraint("custom_cap", CapabilityConstraint(
        capability="custom_cap", parameter="foo", operator=">",
        threshold=42.0, units="units", rationale="test", evidence_rank="A"))
    result = cc.derive(["custom_cap"])
    assert any(c.parameter == "foo" for c in result.constraints)


def test_constraints_result_serializable():
    import json
    cc = CapabilityConstraints()
    result = cc.derive(["conducts_electricity"])
    json.dumps(result.to_dict())


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
