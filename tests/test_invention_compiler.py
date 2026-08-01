"""
Tests for the invention compiler (Layer 0 -> Layer 10).

Per ANTI_ENTROPY.md rule 1 (Write tests first), this file is written
BEFORE the implementation modules. It locks the contract:

  - The compiler must produce all 11 layers, no layer silently skipped.
  - Every layer's output must be a dict matching the schema declared
    in INVENTION_COMPILER.md.
  - Every layer that returns a number MUST also return its evidence
    chain, its assumptions, and its falsification criteria (Law 8
    honesty applied at the module level).
  - The compiler must run end-to-end on a single test invention
    without crashing, and the output must be JSON-serializable.

The reference test invention is "portable_mri" — a deliberately
cross-domain problem (medical imaging + semiconductors + magnetics)
that exercises the synthesizer, the lineage mapper, and the
feasibility scorer simultaneously.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# ----------------------------------------------------------------------
# Schema contracts — every layer MUST emit these keys (NULL is allowed;
# a missing key is a bug).
# ----------------------------------------------------------------------
LAYER_SCHEMAS = {
    0: {"problem", "domain", "motivation", "market", "constraints", "time_horizon"},
    1: {"physics", "chemistry", "biology", "mathematics", "economics",
        "information_theory", "thermodynamics", "control_theory"},
    2: {"prerequisites", "adjacent_technologies", "required_materials",
        "required_infrastructure", "missing_capabilities", "regulatory_constraints"},
    3: {"governing_equations", "boundary_conditions", "assumptions",
        "failure_modes", "optimization_targets"},
    4: {"subsystems", "interfaces", "inputs", "outputs", "tolerances",
        "energy_requirements", "computational_requirements"},
    5: {"monte_carlo", "sensitivity_analysis", "stress_testing", "parameter_ranges"},
    6: {"materials", "suppliers", "tooling", "assembly",
        "quality_control", "scaling_constraints"},
    7: {"capex", "opex", "cost_curve", "market_size", "adoption_model"},
    8: {"hypothesis", "experiments", "measurements",
        "success_criteria", "failure_criteria"},
    9: {"prototype_v1", "prototype_v2", "prototype_v3", "timeline"},
    10: {"blueprint", "patent_landscape", "technical_risks",
         "commercial_risks", "recommended_actions"},
}

# Law 8 honesty contract: every layer that emits a scalar (score,
# probability, etc.) must also emit an evidence block + assumptions +
# falsification_criteria. These are the layers that emit scalars.
LAYERS_WITH_HONESTY_CONTRACT = {3, 5, 7, 10}


# ----------------------------------------------------------------------
# The reference test problem
# ----------------------------------------------------------------------
TEST_PROBLEM = {
    "problem": "Build a portable MRI scanner suitable for rural clinics without cryogenic helium",
    "domain": "medical_imaging",
    "motivation": "Conventional MRI requires $100K+ helium and shielded rooms; rural clinics cannot afford either",
    "market": "global_radiology",
    "constraints": ["cost", "weight", "power", "regulation", "manufacturing"],
    "time_horizon": "5-10 years",
}


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

def test_compiler_imports():
    """The InventionCompiler class must be importable from
    invention_compiler.orchestrator."""
    from invention_compiler.orchestrator import InventionCompiler
    assert InventionCompiler is not None


def test_compiler_runs_end_to_end():
    """The compiler must run Layer 0 -> Layer 10 end-to-end on the
    test problem and return a non-empty dict."""
    from invention_compiler.orchestrator import InventionCompiler
    graph_path = ROOT / "data" / "civilization_graph.json"
    with graph_path.open() as f:
        graph = json.load(f)
    compiler = InventionCompiler(graph=graph)
    result = compiler.compile(TEST_PROBLEM)
    assert result is not None
    assert isinstance(result, dict)
    assert "layers" in result
    assert len(result["layers"]) == 11


def test_every_layer_emits_required_keys():
    """Every layer's output must contain all the keys declared in
    the schema. A NULL value is acceptable; a missing key is a bug."""
    from invention_compiler.orchestrator import InventionCompiler
    graph_path = ROOT / "data" / "civilization_graph.json"
    with graph_path.open() as f:
        graph = json.load(f)
    compiler = InventionCompiler(graph=graph)
    result = compiler.compile(TEST_PROBLEM)
    for layer_num, required_keys in LAYER_SCHEMAS.items():
        layer = result["layers"][layer_num]
        for key in required_keys:
            assert key in layer, \
                f"Layer {layer_num} missing required key {key!r}"


def test_no_layer_silently_skipped():
    """A layer that returns None entirely is a silent skip. Every
    layer must return at least one non-None key."""
    from invention_compiler.orchestrator import InventionCompiler
    graph_path = ROOT / "data" / "civilization_graph.json"
    with graph_path.open() as f:
        graph = json.load(f)
    compiler = InventionCompiler(graph=graph)
    result = compiler.compile(TEST_PROBLEM)
    for layer_num, required_keys in LAYER_SCHEMAS.items():
        layer = result["layers"][layer_num]
        non_null = [k for k in required_keys if layer.get(k) is not None]
        assert non_null, \
            f"Layer {layer_num} is silently skipped — all keys are None"


def test_law8_honesty_contract_on_scalar_layers():
    """Layers that emit scalars (3, 5, 7, 10) must also emit:
      - evidence: the inputs that produced the scalar
      - assumptions: what the scalar assumes
      - falsification_criteria: what would prove the scalar wrong
    """
    from invention_compiler.orchestrator import InventionCompiler
    graph_path = ROOT / "data" / "civilization_graph.json"
    with graph_path.open() as f:
        graph = json.load(f)
    compiler = InventionCompiler(graph=graph)
    result = compiler.compile(TEST_PROBLEM)
    for layer_num in LAYERS_WITH_HONESTY_CONTRACT:
        layer = result["layers"][layer_num]
        # At least one of the layer's keys must carry the honesty block.
        # We check the layer dict itself for a top-level honesty block,
        # OR at least one value that is a dict carrying it.
        has_honesty = False
        if isinstance(layer, dict):
            if "evidence" in layer and "assumptions" in layer \
                    and "falsification_criteria" in layer:
                has_honesty = True
            else:
                for v in layer.values():
                    if isinstance(v, dict) and "evidence" in v \
                            and "assumptions" in v \
                            and "falsification_criteria" in v:
                        has_honesty = True
                        break
        assert has_honesty, (
            f"Layer {layer_num} emits scalars but does not carry the "
            f"Law 8 honesty block (evidence + assumptions + "
            f"falsification_criteria). Per ANTI_ENTROPY.md and "
            f"INVENTION_COMPILER.md, every scalar output must expose "
            f"its chain of reasoning."
        )


def test_result_is_json_serializable():
    """The compiler's output must be JSON-serializable so it can be
    written to evidence/reports/ and read back later for replay."""
    from invention_compiler.orchestrator import InventionCompiler
    graph_path = ROOT / "data" / "civilization_graph.json"
    with graph_path.open() as f:
        graph = json.load(f)
    compiler = InventionCompiler(graph=graph)
    result = compiler.compile(TEST_PROBLEM)
    serialized = json.dumps(result, default=str, indent=2)
    assert len(serialized) > 0
    # And it must round-trip. JSON converts int keys to strings,
    # so we use the string form.
    parsed = json.loads(serialized)
    assert parsed["layers"]["0"]["problem"] == TEST_PROBLEM["problem"]


def test_compiler_does_not_say_this_is_a_good_idea():
    """Per INVENTION_COMPILER.md required rule: the system may never
    output 'this is a good idea.' It must output the complete chain
    of reasoning. Concretely: the compiled output must NOT contain
    a top-level 'verdict' or 'recommendation' key that is a bare
    string like 'good idea' or 'promising'."""
    from invention_compiler.orchestrator import InventionCompiler
    graph_path = ROOT / "data" / "civilization_graph.json"
    with graph_path.open() as f:
        graph = json.load(f)
    compiler = InventionCompiler(graph=graph)
    result = compiler.compile(TEST_PROBLEM)
    forbidden_phrases = ("good idea", "this is promising", "looks great",
                          "highly recommended")
    text = json.dumps(result, default=str).lower()
    for phrase in forbidden_phrases:
        assert phrase not in text, \
            f"Compiler emitted forbidden phrase {phrase!r} — violates " \
            f"INVENTION_COMPILER.md required rule"


def test_compiler_carries_problem_id_and_timestamp():
    """The compiler's output must include metadata for Law 7
    (historical permanence) and Law 8 (replayability)."""
    from invention_compiler.orchestrator import InventionCompiler
    graph_path = ROOT / "data" / "civilization_graph.json"
    with graph_path.open() as f:
        graph = json.load(f)
    compiler = InventionCompiler(graph=graph)
    result = compiler.compile(TEST_PROBLEM)
    assert "problem_id" in result
    assert "timestamp" in result
    assert "writer" in result  # for replayability


def test_compiler_handles_unknown_problem_gracefully():
    """An unknown domain should not crash the compiler. The
    affected layers should return NULL with a reason, per Law 8."""
    from invention_compiler.orchestrator import InventionCompiler
    graph_path = ROOT / "data" / "civilization_graph.json"
    with graph_path.open() as f:
        graph = json.load(f)
    compiler = InventionCompiler(graph=graph)
    result = compiler.compile({
        "problem": "Build a thing",
        "domain": "nonexistent_domain_xyz",
        "motivation": "test",
        "market": "none",
        "constraints": [],
        "time_horizon": "unknown",
    })
    # Every layer must still emit the required keys (None allowed).
    for layer_num, required_keys in LAYER_SCHEMAS.items():
        layer = result["layers"][layer_num]
        for key in required_keys:
            assert key in layer


def test_modules_are_decoupled():
    """Per ANTI_ENTROPY.md rule 'Decouple modules': each module must
    accept the graph as a constructor argument, NOT read it from a
    global. This makes them testable in isolation."""
    from invention_compiler.physics_module import PhysicsModule
    from invention_compiler.chemistry_module import ChemistryModule
    from invention_compiler.dependency_module import DependencyModule
    from invention_compiler.blueprint_module import BlueprintModule
    graph_path = ROOT / "data" / "civilization_graph.json"
    with graph_path.open() as f:
        graph = json.load(f)
    # Each must construct from a graph argument.
    for cls in (PhysicsModule, ChemistryModule, DependencyModule, BlueprintModule):
        engine = cls(graph=graph)
        assert engine is not None


def test_only_verification_engine_is_called_engine():
    """CTO-mandated naming rule: the word 'engine' may only appear in
    module names when the module satisfies: explicit model + empirical
    validation + reproducible results. Currently only verification_engine
    meets this bar.

    This test scans the invention_compiler/ package directory for files
    matching *_engine.py and asserts the only one is
    verification_engine.py. If anyone adds a new *_engine.py without
    satisfying the rule, this test fails loudly.
    """
    import os
    pkg_dir = ROOT / "invention_compiler"
    engine_files = [
        f for f in os.listdir(pkg_dir)
        if f.endswith("_engine.py") and not f.startswith("__")
    ]
    assert engine_files == ["verification_engine.py"], (
        f"CTO naming rule violation: found *_engine.py files that are not "
        f"verification_engine. The 'engine' name is reserved for modules "
        f"with explicit model + empirical validation + reproducible results. "
        f"Found: {engine_files}. Rename to *_module.py until the conditions "
        f"in ANTI_ENTROPY.md are met."
    )


def test_no_class_named_engine_outside_verification():
    """CTO naming rule applied to class names: no class in the
    invention_compiler package may be named XxxEngine unless it lives
    in verification_engine.py."""
    import os
    import re
    pkg_dir = ROOT / "invention_compiler"
    violations = []
    for fname in os.listdir(pkg_dir):
        if not fname.endswith(".py") or fname.startswith("__"):
            continue
        if fname == "verification_engine.py":
            continue
        text = (pkg_dir / fname).read_text()
        # Find class definitions matching XxxEngine.
        for m in re.finditer(r"class\s+(\w*Engine)\b", text):
            violations.append({"file": fname, "class": m.group(1)})
    assert not violations, (
        f"CTO naming rule violation: classes named XxxEngine exist outside "
        f"verification_engine.py. Rename to XxxModule. Violations: {violations}"
    )
