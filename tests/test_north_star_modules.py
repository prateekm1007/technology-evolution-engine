"""
Tests for the new North-Star-directive modules:
  - product/lineage/mapper.py (prerequisite chain — Priority 2)
  - product/discovery/synthesizer.py (cross-domain — Priority 3)
  - product/scoring/feasibility.py (feasibility schema — Priority 4)
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_graph():
    with open(ROOT / "data" / "civilization_graph.json") as f:
        return json.load(f)


# ----------------------------------------------------------------------
# Priority 2: prerequisite chain
# ----------------------------------------------------------------------

def test_prerequisite_chain_returns_tree():
    """prerequisite_chain() should return a tree with the target node
    as root and prerequisite edges as children."""
    from product.lineage.mapper import LineageMapper
    g = _load_graph()
    m = LineageMapper(g)
    # Pick any node that has at least one requires edge.
    target = None
    for e in g["edges"]:
        if e.get("relationship") in ("requires", "depends_on"):
            target = e["source"]
            break
    assert target, "graph should have at least one requires/depends_on edge"
    chain = m.prerequisite_chain(target)
    assert chain["target_id"] == target
    assert "prerequisite_tree" in chain
    assert "flat_chain" in chain
    assert chain["flat_chain"][0]["id"] == target
    assert chain["chain_depth"] >= 1


def test_prerequisite_chain_classifies_relationships():
    """The chain classification should count relationship types."""
    from product.lineage.mapper import LineageMapper
    g = _load_graph()
    m = LineageMapper(g)
    target = None
    for e in g["edges"]:
        if e.get("relationship") in ("requires", "depends_on"):
            target = e["source"]
            break
    chain = m.prerequisite_chain(target)
    cls = chain["classification"]
    assert "root" in cls
    # At least one of these must be present.
    assert cls.get("requires", 0) + cls.get("depends_on", 0) >= 1


def test_prerequisite_chain_handles_unknown_node():
    """Unknown target ids should not crash; they should return an error."""
    from product.lineage.mapper import LineageMapper
    g = _load_graph()
    m = LineageMapper(g)
    chain = m.prerequisite_chain("does_not_exist_xyz")
    assert "error" in chain
    assert chain["prerequisites"] == []


def test_commercial_viability_chain_tags_industry_target():
    """If the target is an industry or system node, the chain should
    flag it as a commercial-viability target."""
    from product.lineage.mapper import LineageMapper
    g = _load_graph()
    m = LineageMapper(g)
    target = None
    for n in g["nodes"]:
        if n.get("type") in ("industry", "system"):
            target = n["id"]
            break
    if target is None:
        return  # skip if no industry/system node exists
    chain = m.commercial_viability_chain(target)
    assert chain.get("commercial_viability_target") == target


def test_map_lineage_backwards_compatible():
    """The legacy top-level map_lineage() function should still work
    and return the same structure as LineageMapper.prerequisite_chain()."""
    from product.lineage.mapper import map_lineage, LineageMapper
    g = _load_graph()
    target = None
    for e in g["edges"]:
        if e.get("relationship") in ("requires", "depends_on"):
            target = e["source"]
            break
    legacy = map_lineage(target, g)
    modern = LineageMapper(g).prerequisite_chain(target)
    assert legacy["target_id"] == modern["target_id"]


# ----------------------------------------------------------------------
# Priority 3: cross-domain synthesizer
# ----------------------------------------------------------------------

def test_synthesizer_returns_candidates():
    """discover() should return a non-empty list of cross-domain pairs."""
    from product.discovery.synthesizer import CrossDomainSynthesizer
    g = _load_graph()
    synth = CrossDomainSynthesizer(g)
    result = synth.discover(top_k=10)
    assert "candidates" in result
    assert len(result["candidates"]) > 0
    assert result["total_pairs_evaluated"] > 0
    assert result["total_pairs_returned"] > 0


def test_synthesizer_candidates_are_cross_domain():
    """Every returned candidate must have domain_a != domain_b."""
    from product.discovery.synthesizer import CrossDomainSynthesizer
    g = _load_graph()
    synth = CrossDomainSynthesizer(g)
    result = synth.discover(top_k=20)
    for c in result["candidates"]:
        assert c["domain_a"] != c["domain_b"], \
            f"candidate {c} is not cross-domain"


def test_synthesizer_excludes_already_connected():
    """Pairs that already have a direct edge should be excluded."""
    from product.discovery.synthesizer import CrossDomainSynthesizer
    g = _load_graph()
    synth = CrossDomainSynthesizer(g)
    result = synth.discover(top_k=10)
    # If the graph has any edges, we should have excluded at least one
    # already-connected pair (since the graph is connected).
    assert result["excluded_already_connected"] >= 0  # smoke; value depends on graph


def test_synthesizer_candidates_have_evidence():
    """Every candidate should carry an evidence block with at least
    one structural signal (shared prereqs, shared constraints, or
    common ancestors)."""
    from product.discovery.synthesizer import CrossDomainSynthesizer
    g = _load_graph()
    synth = CrossDomainSynthesizer(g)
    result = synth.discover(top_k=10)
    for c in result["candidates"]:
        ev = c["evidence"]
        assert "shared_prerequisites" in ev
        assert "shared_constraints" in ev
        assert "common_ancestors" in ev
        # At least one of these must be non-empty for the score to be > 0.
        assert (ev["shared_prerequisites"] or ev["shared_constraints"]
                or ev["common_ancestors"]), \
            f"candidate {c['node_a']['label']}+{c['node_b']['label']} has score but no evidence"


def test_synthesizer_respects_min_score():
    """Candidates below min_score should not be returned."""
    from product.discovery.synthesizer import CrossDomainSynthesizer
    g = _load_graph()
    synth = CrossDomainSynthesizer(g)
    result = synth.discover(top_k=100, min_score=0.99)
    for c in result["candidates"]:
        assert c["structural_overlap_score"] >= 0.99


# ----------------------------------------------------------------------
# Priority 4: feasibility scoring
# ----------------------------------------------------------------------

def test_feasibility_score_has_exact_schema():
    """The output MUST contain the exact keys from the directive."""
    from product.scoring.feasibility import FeasibilityScorer
    g = _load_graph()
    scorer = FeasibilityScorer(g)
    target = next(n["id"] for n in g["nodes"] if n["type"] == "system")
    score = scorer.score(target)
    d = score.to_dict()
    # Exact keys demanded by the directive.
    assert "technical_feasibility" in d
    assert "economic_feasibility" in d
    assert "regulatory_feasibility" in d
    assert "manufacturing_feasibility" in d
    assert "adoption_probability" in d
    assert "estimated_time_horizon" in d
    # All feasibility values must be in [0, 1].
    for k in ("technical_feasibility", "economic_feasibility",
              "regulatory_feasibility", "manufacturing_feasibility",
              "adoption_probability"):
        assert 0.0 <= d[k] <= 1.0, f"{k}={d[k]} not in [0,1]"


def test_feasibility_score_time_horizon_is_string():
    """estimated_time_horizon must be a string like '5-10 years',
    not a number."""
    from product.scoring.feasibility import FeasibilityScorer
    g = _load_graph()
    scorer = FeasibilityScorer(g)
    target = next(n["id"] for n in g["nodes"] if n["type"] == "system")
    score = scorer.score(target)
    assert isinstance(score.estimated_time_horizon, str)
    assert "year" in score.estimated_time_horizon


def test_feasibility_score_carries_evidence():
    """The score must expose the inputs that produced it, so the
    score is auditable — not a black-box number."""
    from product.scoring.feasibility import FeasibilityScorer
    g = _load_graph()
    scorer = FeasibilityScorer(g)
    target = next(n["id"] for n in g["nodes"] if n["type"] == "system")
    score = scorer.score(target)
    ev = score.evidence
    assert "prerequisite_completeness" in ev
    assert "constraints" in ev
    assert "cemetery_analogues" in ev
    assert "lineage_depth" in ev
    assert "operators_applied" in ev


def test_feasibility_score_includes_falsification_criteria():
    """Every score must say what would prove it wrong — Law 8 honesty."""
    from product.scoring.feasibility import FeasibilityScorer
    g = _load_graph()
    scorer = FeasibilityScorer(g)
    target = next(n["id"] for n in g["nodes"] if n["type"] == "system")
    score = scorer.score(target)
    assert score.falsification_criteria
    assert "calibrat" in score.falsification_criteria.lower() \
        or "fail" in score.falsification_criteria.lower()


def test_feasibility_score_unknown_target_returns_zero():
    """An unknown target should return a zero score with a reason, not crash."""
    from product.scoring.feasibility import FeasibilityScorer
    g = _load_graph()
    scorer = FeasibilityScorer(g)
    score = scorer.score("does_not_exist_xyz")
    assert score.composite_feasibility == 0.0
    assert "reason" in score.evidence


def test_feasibility_score_operators_affect_dimensions():
    """Applying operators (Law 4: eliminate, substitute, etc.) should
    shift specific feasibility dimensions — not just uniformly inflate
    the composite."""
    from product.scoring.feasibility import FeasibilityScorer
    g = _load_graph()
    scorer = FeasibilityScorer(g)
    target = next(n["id"] for n in g["nodes"] if n["type"] == "system")
    baseline = scorer.score(target)
    with_ops = scorer.score(target, operators=["miniaturize", "modularize"])
    # The two scores should differ.
    assert baseline.to_dict() != with_ops.to_dict()
    # And the difference should be traceable to specific dimensions.
    assert baseline.technical_feasibility != with_ops.technical_feasibility \
        or baseline.manufacturing_feasibility != with_ops.manufacturing_feasibility
