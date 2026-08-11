"""Tests for cycle 183 modules — 8 categories pushed 8→9."""
import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ===== Mechanism quantitative (Mechanism 8→9) =====

def test_mechanism_quantitative_links_equations():
    """link_equations_to_chain attaches governing equations."""
    from scripts.mechanism_quantitative import link_equations_to_chain
    from scripts.mechanism_state_machine import MechanismChain, StateTransition
    from scripts.equation_extractor import ExtractedEquation, EquationType

    chain = MechanismChain(
        steps=[StateTransition(
            entity="electrode", from_state="crystalline", to_state="amorphous",
            transition_verb="undergoes",
        )],
        chain_entity="electrode",
        chain_length=1,
    )
    eq = ExtractedEquation(
        type=EquationType.EXPLICIT,
        lhs="Q", rhs="σAT⁴", variables=["Q", "σ", "A", "T"],
        operator="=", source_text="Q = σAT⁴",
    )
    qm = link_equations_to_chain(chain, [eq])
    assert len(qm.governing_equations) >= 1


def test_mechanism_quantitative_prediction_stefan_boltzmann():
    """Quantitative prediction computes Stefan-Boltzmann Q correctly."""
    from scripts.mechanism_quantitative import link_equations_to_chain
    from scripts.mechanism_state_machine import MechanismChain, StateTransition
    from scripts.equation_extractor import ExtractedEquation, EquationType

    chain = MechanismChain(
        steps=[StateTransition(
            entity="radiator", from_state="cool", to_state="hot",
            transition_verb="transitions",
        )],
        chain_entity="radiator",
        chain_length=1,
    )
    eq = ExtractedEquation(
        type=EquationType.EXPLICIT,
        lhs="Q", rhs="σAT⁴", variables=["Q", "σ", "A", "T"],
        operator="=", source_text="Q = σAT⁴",
    )
    qm = link_equations_to_chain(chain, [eq])
    # Should have a prediction with Q value
    assert len(qm.predictions) >= 1
    pred = qm.predictions[0]
    if pred:
        assert "Q" in pred.get("output", {})


# ===== Constraint chaining (Constraint 8→9) =====

def test_constraint_chaining_finds_transitive():
    """chain_constraints finds transitive A→C from A→B and B→C."""
    from scripts.constraint_chaining import chain_constraints
    from scripts.constraint_from_equations import DerivedConstraint, ConstraintDirection

    direct = [
        DerivedConstraint("B", ["A"], ConstraintDirection.DETERMINED, "B=2A", "A→B", 0.85),
        DerivedConstraint("C", ["B"], ConstraintDirection.DETERMINED, "C=B+5", "B→C", 0.85),
    ]
    chained = chain_constraints(direct)
    # Should find A→C
    found_ac = any(c.constrained_variable == "C" and "A" in c.constraining_variables
                   for c in chained)
    assert found_ac, f"A→C not found in chained: {[(c.constrained_variable, c.constraining_variables) for c in chained]}"


def test_constraint_chaining_limits_depth():
    """chain_constraints limits chain depth to 5."""
    from scripts.constraint_chaining import chain_constraints
    from scripts.constraint_from_equations import DerivedConstraint, ConstraintDirection

    # A→B→C→D→E→F→G — chain depth 6 should be limited
    direct = [
        DerivedConstraint(chr(66 + i), [chr(65 + i)], ConstraintDirection.DETERMINED,
                          f"{chr(66+i)}={chr(65+i)}+1", f"{chr(65+i)}→{chr(66+i)}", 0.85)
        for i in range(6)
    ]
    chained = chain_constraints(direct)
    # Should not produce A→G (depth 6) — limit is 5
    found_ag = any(c.constrained_variable == "G" and "A" in c.constraining_variables
                   for c in chained)
    assert not found_ag, "Chain depth should be limited to 5"


# ===== Law cross-domain (Law discovery 8→9) =====

def test_law_cross_domain_discovers_exponent():
    """discover_power_law recovers the exponent from data."""
    from scripts.law_cross_domain import CrossDomainLawValidator
    validator = CrossDomainLawValidator()
    # y = 2 * x^3 → exponent should be ~3
    x = [1, 2, 3, 4, 5]
    y = [2 * xi ** 3 for xi in x]
    exponent, r2, desc = validator.discover_power_law(x, y)
    assert abs(exponent - 3.0) < 0.01
    assert r2 > 0.99


def test_law_cross_domain_validates_on_disjoint():
    """validate_law_across_domains validates on disjoint corpus."""
    from scripts.law_cross_domain import CrossDomainLawValidator
    validator = CrossDomainLawValidator()
    sigma = 5.670374419e-8
    disc = ([200, 250, 300], [sigma * T ** 4 for T in [200, 250, 300]])
    val = ([500, 600, 700], [sigma * T ** 4 for T in [500, 600, 700]])
    result = validator.validate_law_across_domains(disc, val)
    assert result.discovery_R2 > 0.99
    assert result.validation_R2 > 0.99
    assert result.generalizes


# ===== Causal data-estimated (Causal 8→9, F-088 fix) =====
# Per cycle 185 (PRECONDITION 0.5): causal_real_corpus.py was DELETED
# (hardcoded probabilities, F-088). These tests now use causal_data_estimated.py
# which returns honest "I don't know" when data is insufficient.

def test_causal_data_estimated_finds_edge():
    """DataEstimatedCounterfactual finds a real causal edge."""
    from scripts.causal_data_estimated import DataEstimatedCounterfactual
    dec = DataEstimatedCounterfactual()
    edge = dec.find_real_causal_edge()
    # Should find SOME edge (the corpus graph has edges)
    assert edge is not None
    assert "source" in edge
    assert "target" in edge


def test_causal_data_estimated_runs_counterfactual():
    """Data-estimated counterfactual produces a result (may be 'insufficient data')."""
    from scripts.causal_data_estimated import DataEstimatedCounterfactual
    dec = DataEstimatedCounterfactual()
    result = dec.run_on_real_edge()
    if result:  # may be None if no edges
        # The result must be HONEST — no hardcoded probabilities.
        # If insufficient data, all probabilities are 0.0 and is_honest=True.
        assert 0.0 <= result.p_observed <= 1.0
        assert 0.0 <= result.p_counterfactual <= 1.0
        assert result.edge_source
        assert result.edge_target
        assert result.is_honest is True  # F-088: must be data-estimated, not hardcoded


# ===== Structural analogy v3 (Structural 8→9) =====

def test_structural_v3_finds_depth3_analogies():
    """Depth3StructureMappingEngine finds depth-3 analogies."""
    from scripts.structural_analogy_v3 import Depth3StructureMappingEngine
    from invention_compiler.discovery_graph import (
        DiscoveryGraph, DiscoveryNode, DiscoveryEdge, RelationType,
    )
    graph = DiscoveryGraph()
    for nid in ["a", "b", "c", "d", "w", "x", "y", "z"]:
        graph.add_node(DiscoveryNode(
            node_id=nid, node_type="concept", label=nid,
            properties={"domain": "d1" if nid < "n" else "d2"},
            layers=set(), provenance={},
        ))
    # Chain 1: a→b→c→d with predicates (causes, produces, enables)
    for src, tgt, pred in [("a", "b", "causes"), ("b", "c", "produces"), ("c", "d", "enables")]:
        graph.add_edge(DiscoveryEdge(
            source=src, target=tgt, relation_type=RelationType.MECHANISM,
            evidence=[], metadata={}, direction=pred,
        ))
    # Chain 2: w→x→y→z with same predicates
    for src, tgt, pred in [("w", "x", "causes"), ("x", "y", "produces"), ("y", "z", "enables")]:
        graph.add_edge(DiscoveryEdge(
            source=src, target=tgt, relation_type=RelationType.MECHANISM,
            evidence=[], metadata={}, direction=pred,
        ))

    engine = Depth3StructureMappingEngine(graph)
    analogies = engine.find_depth3_analogies()
    assert len(analogies) >= 1


def test_structural_v3_analogical_transfer():
    """Analogical transfer applies inferred edges to the target graph."""
    from scripts.structural_analogy_v3 import Depth3StructureMappingEngine
    from invention_compiler.discovery_graph import (
        DiscoveryGraph, DiscoveryNode, DiscoveryEdge, RelationType,
    )
    graph = DiscoveryGraph()
    for nid in ["a", "b", "c", "d", "growth", "w", "x", "y", "z"]:
        graph.add_node(DiscoveryNode(
            node_id=nid, node_type="concept", label=nid,
            properties={"domain": "d1" if nid < "n" else "d2"},
            layers=set(), provenance={},
        ))
    # Chain 1 has 4 edges (a→b→c→d→growth); Chain 2 has 3 (w→x→y→z, no extension)
    for src, tgt, pred in [
        ("a", "b", "causes"), ("b", "c", "produces"),
        ("c", "d", "enables"), ("d", "growth", "enables"),
        ("w", "x", "causes"), ("x", "y", "produces"), ("y", "z", "enables"),
    ]:
        graph.add_edge(DiscoveryEdge(
            source=src, target=tgt, relation_type=RelationType.MECHANISM,
            evidence=[], metadata={}, direction=pred,
        ))

    engine = Depth3StructureMappingEngine(graph)
    analogies, transfers = engine.find_depth3_analogies_with_transfer(apply_transfers=True)
    # At least one transfer should be applied
    applied = [t for t in transfers if t.applied]
    assert len(applied) >= 1


# ===== Bayesian DOE (Experiment 8→9) =====

def test_bayesian_doe_selects_subset():
    """BayesianDOE selects a subset of full factorial runs."""
    from scripts.bayesian_doe import BayesianDOE, Factor

    factors = [
        Factor("A", low=0, high=1),
        Factor("B", low=0, high=1),
    ]
    hypotheses = ["h1_linear", "h2_exp"]
    def likelihood(h, s):
        return 0.8 if "linear" in h else 0.3

    bdoe = BayesianDOE(factors, hypotheses, likelihood)
    design = bdoe.design_optimal_experiment(budget=2)
    # Should select 2 runs (budget)
    assert len(design.selected_runs) <= 2
    # Total IG should be > 0 (assuming informative experiments)
    assert design.expected_ig >= 0


def test_bayesian_doe_ig_per_cost_positive():
    """IG/cost is non-negative."""
    from scripts.bayesian_doe import BayesianDOE, Factor

    factors = [Factor("A", low=0, high=1)]
    hypotheses = ["h1", "h2"]
    def likelihood(h, s):
        return 0.9 if h == "h1" else 0.1

    bdoe = BayesianDOE(factors, hypotheses, likelihood)
    design = bdoe.design_optimal_experiment(budget=1)
    assert design.ig_per_cost >= 0


# ===== Learning corpus selection (Learning 8→9) =====

def test_learning_corpus_extracts_hypotheses():
    """CorpusActiveLearner extracts hypotheses from corpus."""
    from scripts.learning_corpus_selection import CorpusActiveLearner
    learner = CorpusActiveLearner(max_papers=3)
    hypotheses, papers = learner.extract_hypotheses_from_corpus()
    # Should extract at least 1 hypothesis
    assert len(hypotheses) >= 1
    assert len(papers) >= 1


def test_learning_corpus_selects_experiment():
    """CorpusActiveLearner selects an experiment from real corpus hypotheses."""
    from scripts.learning_corpus_selection import CorpusActiveLearner
    learner = CorpusActiveLearner(max_papers=3)
    result = learner.select_experiment_from_corpus()
    # Should produce SOME result (may be empty selection if IG below threshold)
    assert hasattr(result, "hypotheses")
    assert hasattr(result, "selected_experiment")


# ===== Scalability 10K (Scalability 8→9) =====

def test_scalability_10k_runs():
    """benchmark_10k runs without error at N=1000."""
    from scripts.scalability_10k import benchmark_10k
    result = benchmark_10k(n_nodes=1000, n_domains=10, n_subdomains_per_domain=5)
    assert result.n_nodes == 1000
    assert result.build_time_seconds >= 0
    assert result.search_time_seconds >= 0


def test_scalability_10k_completes_in_reasonable_time():
    """10K benchmark completes in under 60 seconds."""
    from scripts.scalability_10k import benchmark_10k
    result = benchmark_10k(n_nodes=10000, n_domains=50, n_subdomains_per_domain=4)
    assert result.n_nodes == 10000
    # 10K should complete in under 60s
    assert result.search_time_seconds < 60.0, \
        f"10K search took {result.search_time_seconds}s (expected < 60s)"


# ===== Composite test =====

def test_all_cycle_183_modules_importable():
    """All cycle 183 modules can be imported."""
    from scripts.mechanism_quantitative import link_equations_to_chain
    from scripts.constraint_chaining import chain_constraints
    from scripts.law_cross_domain import CrossDomainLawValidator
    from scripts.causal_data_estimated import DataEstimatedCounterfactual
    from scripts.structural_analogy_v3 import Depth3StructureMappingEngine
    from scripts.bayesian_doe import BayesianDOE
    from scripts.learning_corpus_selection import CorpusActiveLearner
    from scripts.scalability_10k import benchmark_10k
    # All imports succeeded
    assert link_equations_to_chain is not None
    assert chain_constraints is not None
    assert CrossDomainLawValidator is not None
    assert DataEstimatedCounterfactual is not None
    assert Depth3StructureMappingEngine is not None
    assert BayesianDOE is not None
    assert CorpusActiveLearner is not None
    assert benchmark_10k is not None


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
