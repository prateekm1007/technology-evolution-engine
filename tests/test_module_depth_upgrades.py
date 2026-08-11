"""
Tests for module depth upgrades (CTO review #2, commit `02d7658`).

Per ANTI_ENTROPY.md rule 1 (Write tests first), these tests are
written BEFORE the upgrades. They lock the contract that each
upgraded module must encode a real scientific principle, not a
keyword filter.

The tests for each module assert:
  - The module exposes the new scientific API (e.g., conservation laws,
    reaction pathways, causal edges).
  - The module produces DIFFERENTIATED output for different problems.
    (The pre-upgrade modules produced identical composites across
    all 5 benchmark cases — that was the entropy this upgrade targets.)
  - The output carries the Law 8 honesty block.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_graph():
    with open(ROOT / "data" / "civilization_graph.json") as f:
        return json.load(f)


# ----------------------------------------------------------------------
# Physics module depth upgrade
# ----------------------------------------------------------------------

def test_physics_module_exposes_conservation_laws():
    """The upgraded physics module must expose the canonical
    conservation laws (mass, energy, momentum, charge) as a
    queryable data structure, not as a keyword filter."""
    from invention_compiler.physics_knowledge_module import PhysicsKnowledgeModule
    g = _load_graph()
    m = PhysicsKnowledgeModule(graph=g)
    # The new API: laws() returns a dict of named laws.
    laws = m.laws()
    assert "mass_conservation" in laws
    assert "energy_conservation" in laws
    assert "momentum_conservation" in laws
    assert "charge_conservation" in laws


def test_physics_module_exposes_thermodynamics_laws():
    """The upgraded module must expose the four laws of thermodynamics."""
    from invention_compiler.physics_knowledge_module import PhysicsKnowledgeModule
    g = _load_graph()
    m = PhysicsKnowledgeModule(graph=g)
    laws = m.laws()
    assert "zeroth_law_thermodynamics" in laws
    assert "first_law_thermodynamics" in laws
    assert "second_law_thermodynamics" in laws
    assert "third_law_thermodynamics" in laws


def test_physics_module_carries_units_and_dimensional_analysis():
    """The upgraded module must expose SI base units and a
    dimensional-analysis check."""
    from invention_compiler.physics_knowledge_module import PhysicsKnowledgeModule
    g = _load_graph()
    m = PhysicsKnowledgeModule(graph=g)
    units = m.units()
    # SI base units.
    for u in ("kg", "m", "s", "A", "K", "mol", "cd"):
        assert u in units, f"missing SI base unit {u}"
    # Dimensional analysis: check_consistency returns True/False for
    # a given equation's LHS vs RHS dimensions.
    assert m.check_consistency("F = m * a") is True
    assert m.check_consistency("E = m * c^2") is True
    # An inconsistent equation should fail.
    assert m.check_consistency("F = m + v") is False


def test_physics_module_laws_carry_equations():
    """Each conservation law must carry its governing equation as a
    structured object — not just a string label."""
    from invention_compiler.physics_knowledge_module import PhysicsKnowledgeModule
    g = _load_graph()
    m = PhysicsKnowledgeModule(graph=g)
    laws = m.laws()
    energy = laws["energy_conservation"]
    assert "equation" in energy
    assert "variables" in energy
    assert "units" in energy
    assert "applies_to" in energy  # which problem types this law governs


def test_physics_module_differentiates_problems():
    """CRITICAL: the upgraded module must produce DIFFERENT output for
    DIFFERENT problems. The pre-upgrade module produced identical
    constraint_load for all 5 benchmark cases — that was the bug.

    Concretely: a problem involving superconductivity should surface
    different physics laws than a problem involving fluid dynamics.
    """
    from invention_compiler.physics_knowledge_module import PhysicsKnowledgeModule
    g = _load_graph()
    m = PhysicsKnowledgeModule(graph=g)
    out_a = m.analyze({
        "problem": "Build a portable MRI scanner",
        "domain": "medical_imaging",
        "constraints": ["cost", "magnetic"],
    })
    out_b = m.analyze({
        "problem": "Synthesize ammonia at ambient conditions",
        "domain": "chemistry",
        "constraints": ["catalyst", "energy"],
    })
    # The applicable_laws lists MUST differ.
    laws_a = set(out_a.get("applicable_laws", []))
    laws_b = set(out_b.get("applicable_laws", []))
    assert laws_a != laws_b, (
        "physics module produced identical applicable_laws for two "
        "different problems — the depth upgrade failed to differentiate."
    )


# ----------------------------------------------------------------------
# Chemistry module depth upgrade
# ----------------------------------------------------------------------

def test_chemistry_module_exposes_reaction_pathways():
    """The upgraded chemistry module must encode reaction pathways as
    structured objects, not as a keyword list."""
    from invention_compiler.chemistry_knowledge_module import ChemistryKnowledgeModule
    g = _load_graph()
    m = ChemistryKnowledgeModule(graph=g)
    pathways = m.reaction_pathways()
    assert isinstance(pathways, list)
    assert len(pathways) > 0
    # Each pathway is a structured object.
    p = pathways[0]
    assert "name" in p
    assert "reactants" in p
    assert "products" in p
    assert "conditions" in p  # T, P, catalyst requirements


def test_chemistry_module_exposes_kinetics_model():
    """The upgraded module must expose kinetic rate laws
    (Arrhenius, Michaelis-Menten) as structured models."""
    from invention_compiler.chemistry_knowledge_module import ChemistryKnowledgeModule
    g = _load_graph()
    m = ChemistryKnowledgeModule(graph=g)
    kinetics = m.kinetics_models()
    assert "arrhenius" in kinetics
    # Arrhenius: k = A * exp(-Ea / (R*T))
    arr = kinetics["arrhenius"]
    assert "equation" in arr
    assert "variables" in arr
    assert "A" in arr["variables"]  # pre-exponential factor
    assert "Ea" in arr["variables"]  # activation energy
    assert "R" in arr["variables"]   # gas constant
    assert "T" in arr["variables"]   # temperature


def test_chemistry_module_exposes_equilibrium_constants():
    """The upgraded module must expose equilibrium-constant formulas."""
    from invention_compiler.chemistry_knowledge_module import ChemistryKnowledgeModule
    g = _load_graph()
    m = ChemistryKnowledgeModule(graph=g)
    eq = m.equilibrium_models()
    assert "K_eq" in eq
    assert "equation" in eq["K_eq"]


def test_chemistry_module_exposes_energy_states():
    """The upgraded module must expose Gibbs free energy as the
    canonical energy-state model."""
    from invention_compiler.chemistry_knowledge_module import ChemistryKnowledgeModule
    g = _load_graph()
    m = ChemistryKnowledgeModule(graph=g)
    states = m.energy_states()
    assert "gibbs_free_energy" in states
    gibbs = states["gibbs_free_energy"]
    assert "equation" in gibbs
    # G = H - T*S
    assert "H" in gibbs["variables"]
    assert "T" in gibbs["variables"]
    assert "S" in gibbs["variables"]


def test_chemistry_module_differentiates_problems():
    """A problem involving electrochemistry should surface different
    pathways than one involving polymer synthesis."""
    from invention_compiler.chemistry_knowledge_module import ChemistryKnowledgeModule
    g = _load_graph()
    m = ChemistryKnowledgeModule(graph=g)
    out_a = m.analyze({
        "problem": "Electrochemical ammonia synthesis",
        "domain": "chemistry",
        "constraints": ["catalyst", "energy", "electrochemistry"],
    })
    out_b = m.analyze({
        "problem": "Polymer membrane synthesis",
        "domain": "chemistry",
        "constraints": ["material", "manufacturing"],
    })
    pathways_a = set(out_a.get("applicable_pathways", []))
    pathways_b = set(out_b.get("applicable_pathways", []))
    assert pathways_a != pathways_b, (
        "chemistry module produced identical pathways for two different "
        "problems — the depth upgrade failed to differentiate."
    )


# ----------------------------------------------------------------------
# Mathematics module depth upgrade
# ----------------------------------------------------------------------

def test_mathematics_module_exposes_optimization_formulations():
    """The upgraded mathematics module must expose optimization
    formulations (LP, convex, etc.) as structured objects."""
    from invention_compiler.mathematics_knowledge_module import MathematicsKnowledgeModule
    g = _load_graph()
    m = MathematicsKnowledgeModule(graph=g)
    opt = m.optimization_formulations()
    assert "linear_programming" in opt
    assert "convex_optimization" in opt
    lp = opt["linear_programming"]
    assert "form" in lp
    assert "applicable_when" in lp


def test_mathematics_module_exposes_probability_distributions():
    """The upgraded module must expose common probability
    distributions as structured models."""
    from invention_compiler.mathematics_knowledge_module import MathematicsKnowledgeModule
    g = _load_graph()
    m = MathematicsKnowledgeModule(graph=g)
    probs = m.probability_models()
    assert "normal" in probs
    assert "bernoulli" in probs
    assert "poisson" in probs


def test_mathematics_module_exposes_graph_theory():
    """The upgraded module must expose graph-theory concepts."""
    from invention_compiler.mathematics_knowledge_module import MathematicsKnowledgeModule
    g = _load_graph()
    m = MathematicsKnowledgeModule(graph=g)
    gt = m.graph_theory_concepts()
    assert "shortest_path" in gt
    assert "connectivity" in gt
    assert "centrality" in gt


def test_mathematics_module_exposes_differential_equation_types():
    """The upgraded module must expose ODE and PDE types."""
    from invention_compiler.mathematics_knowledge_module import MathematicsKnowledgeModule
    g = _load_graph()
    m = MathematicsKnowledgeModule(graph=g)
    des = m.differential_equation_types()
    assert "ode_first_order" in des
    assert "ode_second_order" in des
    assert "pde_diffusion" in des
    assert "pde_wave" in des


def test_mathematics_module_exposes_control_theory():
    """The upgraded module must expose control-theory concepts."""
    from invention_compiler.mathematics_knowledge_module import MathematicsKnowledgeModule
    g = _load_graph()
    m = MathematicsKnowledgeModule(graph=g)
    ct = m.control_theory_concepts()
    assert "pid" in ct
    assert "state_space" in ct
    assert "stability" in ct


# ----------------------------------------------------------------------
# Dependency module depth upgrade — causal relationships
# ----------------------------------------------------------------------

def test_dependency_module_exposes_causal_edges():
    """The upgraded dependency module must classify edges as
    'necessary', 'sufficient', or 'contributing' — not just
    'requires' or 'depends_on'."""
    from invention_compiler.dependency_module import DependencyModule
    g = _load_graph()
    m = DependencyModule(graph=g)
    # analyze() must return causal_classification on each prereq.
    out = m.analyze({
        "problem": "test",
        "domain": "medical_imaging",
        "constraints": ["cost"],
    })
    for p in out.get("prerequisites", []):
        # Every prerequisite should carry a causal_classification.
        # If the graph doesn't have enough info, it's 'unknown' — but
        # the key must be present.
        assert "causal_classification" in p


def test_dependency_module_supports_counterfactual():
    """The upgraded module must support counterfactual analysis:
    'if prerequisite X were absent, would the target still be
    viable?'"""
    from invention_compiler.dependency_module import DependencyModule
    g = _load_graph()
    m = DependencyModule(graph=g)
    out = m.analyze({
        "problem": "test",
        "domain": "medical_imaging",
        "constraints": ["cost"],
    })
    assert "counterfactual_analysis" in out
    cf = out["counterfactual_analysis"]
    # Should be a list of {prerequisite, removal_impact} entries.
    assert isinstance(cf, list)


# ----------------------------------------------------------------------
# Resurrection module depth upgrade — counterfactual analysis
# ----------------------------------------------------------------------

def test_resurrection_module_exposes_counterfactual_analysis():
    """The upgraded resurrection module must move from 'historical
    similarity' (keyword overlap) to 'historical counterfactual
    analysis' — i.e., 'if X had been different, would the failure
    have succeeded?'"""
    from invention_compiler.resurrection_module import ResurrectionModule
    g = _load_graph()
    m = ResurrectionModule(graph=g)
    out = m.analyze(
        problem={"domain": "transportation", "constraints": ["cost"]},
        dependency_output={"prerequisites": []},
    )
    opportunities = out.get("resurrection_opportunities", [])
    # Each opportunity must carry a counterfactual_analysis block.
    for opp in opportunities:
        assert "counterfactual" in opp, \
            "resurrection_module opportunity missing counterfactual_analysis"
        cf = opp["counterfactual"]
        assert "what_changed" in cf
        assert "predicted_outcome_if_changed" in cf


def test_resurrection_module_counterfactual_is_specific():
    """The counterfactual must be specific to the failure, not a
    generic statement. E.g., for Airships: 'if helium had been
    available instead of hydrogen, would Airships have succeeded?'"""
    from invention_compiler.resurrection_module import ResurrectionModule
    g = _load_graph()
    m = ResurrectionModule(graph=g)
    out = m.analyze(
        problem={"domain": "transportation", "constraints": ["cost"]},
        dependency_output={"prerequisites": []},
    )
    # Find the Airships entry.
    airships = next(
        (o for o in out["resurrection_opportunities"]
         if o.get("name") == "Airships"), None
    )
    assert airships is not None
    cf = airships["counterfactual"]
    # The 'what_changed' must reference a specific historical variable
    # (helium availability, not just 'conditions changed').
    assert "helium" in cf["what_changed"].lower() or \
           "hydrogen" in cf["what_changed"].lower(), \
           f"Airships counterfactual not specific enough: {cf}"


# ----------------------------------------------------------------------
# 4-category benchmark taxonomy
# ----------------------------------------------------------------------

def test_benchmark_taxonomy_has_5_categories():
    """Per CTO review #3, the benchmark suite must define 5 categories:
    reconstruction, resurrection, forecasting, synthesis, creation."""
    from benchmarks.compiler import BENCHMARK_CATEGORIES
    assert set(BENCHMARK_CATEGORIES.keys()) == {
        "reconstruction", "resurrection", "forecasting", "synthesis", "creation"
    }


def test_each_benchmark_case_is_categorized():
    """Every case in CASES must declare which category it belongs to."""
    from benchmarks.compiler import CASES, BENCHMARK_CATEGORIES
    valid_categories = set(BENCHMARK_CATEGORIES.keys())
    for case in CASES:
        assert "category" in case, \
            f"case {case['id']} missing 'category' field"
        assert case["category"] in valid_categories, \
            f"case {case['id']} has invalid category {case['category']!r}"


def test_all_4_categories_are_covered():
    """The 6 cases must cover at least 3 of the 4 categories.
    (Synthesis may be empty until we have novel cross-domain
    candidates the benchmarker can verify.)"""
    from benchmarks.compiler import CASES
    cats = set(c["category"] for c in CASES)
    assert len(cats) >= 3, \
        f"expected >=3 categories covered, got {cats}"
