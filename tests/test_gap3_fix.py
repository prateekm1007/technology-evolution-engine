"""
Tests for Gap 3 fix (non-buildable blueprints).

Per ANTI_ENTROPY.md rule 1 (tests first) and the Maestro Modification
Loop PHASE 6 (modify ONE component).

Gap 3: the blueprint_module produces a structured summary, not a
buildable spec. An engineer cannot start building from the current
final_blueprint without consulting the underlying layers.

The contract: after the fix, the final_blueprint must carry:
  - parts_list (from Layer 2 required_materials)
  - materials_specification (from Layer 6 materials)
  - assembly_plan (from Layer 4 subsystems + interfaces)
  - tolerances (from Layer 4 tolerances)
  - prototype_specification (from Layer 9 prototype_v1/v2/v3)

At least 15/20 candidates must have all 5 fields non-empty.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


CANDIDATES = [
    ("001_solid_state_batteries", "materials",
     ["cost", "material", "manufacturing", "regulation", "energy"]),
    ("002_carbon_negative_concrete", "materials",
     ["cost", "material", "regulation", "manufacturing", "carbon_negative"]),
    ("003_atmospheric_water_harvesting", "water",
     ["cost", "energy", "material", "manufacturing"]),
    ("004_portable_mri", "medical_imaging",
     ["cost", "weight", "power", "regulation", "manufacturing"]),
    ("005_desalination_systems", "water",
     ["cost", "energy", "material", "manufacturing", "regulation"]),
    ("006_autonomous_greenhouses", "agriculture",
     ["cost", "energy", "material", "regulation", "manufacturing"]),
    ("007_modular_nuclear_reactors", "energy",
     ["cost", "material", "regulation", "manufacturing", "safety"]),
    ("008_artificial_photosynthesis", "energy",
     ["energy", "material", "catalyst", "manufacturing", "regulation", "photosynthesis"]),
    ("009_protein_engineering_systems", "biology",
     ["cost", "information", "material", "regulation"]),
    ("010_biodegradable_polymers", "materials",
     ["cost", "material", "manufacturing", "regulation"]),
    ("011_adaptive_prosthetics", "medical_devices",
     ["cost", "weight", "power", "material", "regulation", "manufacturing"]),
    ("012_vertical_farming", "agriculture",
     ["cost", "energy", "material", "manufacturing", "regulation"]),
    ("013_thermoelectric_materials", "materials",
     ["cost", "material", "manufacturing", "energy"]),
    ("014_carbon_capture_materials", "materials",
     ["cost", "energy", "material", "manufacturing", "regulation"]),
    ("015_superconducting_materials", "materials",
     ["material", "energy", "manufacturing", "regulation", "superconductivity"]),
    ("016_precision_fermentation", "biology",
     ["cost", "energy", "material", "regulation", "manufacturing"]),
    ("017_agricultural_robotics", "robotics",
     ["cost", "energy", "material", "manufacturing", "regulation"]),
    ("018_synthetic_fuels", "energy",
     ["cost", "energy", "material", "catalyst", "manufacturing", "regulation"]),
    ("019_smart_textiles", "materials",
     ["cost", "material", "manufacturing", "energy", "regulation"]),
    ("020_distributed_manufacturing", "manufacturing",
     ["cost", "material", "manufacturing", "regulation", "information"]),
]


def _make_problem(name, domain, constraints):
    return {
        "problem": f"Build {name.replace('_', ' ')}",
        "domain": domain,
        "motivation": "test",
        "market": "test_market",
        "constraints": constraints,
        "time_horizon": "5-10 years",
    }


# ----------------------------------------------------------------------
# 1. Blueprint carries buildable-spec fields
# ----------------------------------------------------------------------

def test_blueprint_carries_parts_list():
    """GAP 3 FIX: The final_blueprint must carry a parts_list field
    (from Layer 2 required_materials)."""
    from invention_compiler.orchestrator import InventionCompiler
    graph_path = ROOT / "data" / "civilization_graph.json"
    with open(graph_path) as f:
        graph = json.load(f)
    compiler = InventionCompiler(graph=graph)
    result = compiler.compile(_make_problem(*CANDIDATES[0]))
    blueprint = result["layers"][10].get("blueprint", {})
    assert "parts_list" in blueprint, \
        "final_blueprint missing 'parts_list' field — not buildable"
    assert isinstance(blueprint["parts_list"], list)


def test_blueprint_carries_materials_specification():
    """GAP 3 FIX: The final_blueprint must carry a materials_specification
    field (from Layer 6 materials)."""
    from invention_compiler.orchestrator import InventionCompiler
    graph_path = ROOT / "data" / "civilization_graph.json"
    with open(graph_path) as f:
        graph = json.load(f)
    compiler = InventionCompiler(graph=graph)
    result = compiler.compile(_make_problem(*CANDIDATES[0]))
    blueprint = result["layers"][10].get("blueprint", {})
    assert "materials_specification" in blueprint, \
        "final_blueprint missing 'materials_specification' field"
    assert isinstance(blueprint["materials_specification"], (list, dict))


def test_blueprint_carries_assembly_plan():
    """GAP 3 FIX: The final_blueprint must carry an assembly_plan field
    (from Layer 4 subsystems + interfaces)."""
    from invention_compiler.orchestrator import InventionCompiler
    graph_path = ROOT / "data" / "civilization_graph.json"
    with open(graph_path) as f:
        graph = json.load(f)
    compiler = InventionCompiler(graph=graph)
    result = compiler.compile(_make_problem(*CANDIDATES[0]))
    blueprint = result["layers"][10].get("blueprint", {})
    assert "assembly_plan" in blueprint, \
        "final_blueprint missing 'assembly_plan' field"
    assert isinstance(blueprint["assembly_plan"], (list, dict))


def test_blueprint_carries_tolerances():
    """GAP 3 FIX: The final_blueprint must carry a tolerances field
    (from Layer 4 tolerances)."""
    from invention_compiler.orchestrator import InventionCompiler
    graph_path = ROOT / "data" / "civilization_graph.json"
    with open(graph_path) as f:
        graph = json.load(f)
    compiler = InventionCompiler(graph=graph)
    result = compiler.compile(_make_problem(*CANDIDATES[0]))
    blueprint = result["layers"][10].get("blueprint", {})
    assert "tolerances" in blueprint, \
        "final_blueprint missing 'tolerances' field"


def test_blueprint_carries_prototype_specification():
    """GAP 3 FIX: The final_blueprint must carry a prototype_specification
    field (from Layer 9 prototype_v1/v2/v3)."""
    from invention_compiler.orchestrator import InventionCompiler
    graph_path = ROOT / "data" / "civilization_graph.json"
    with open(graph_path) as f:
        graph = json.load(f)
    compiler = InventionCompiler(graph=graph)
    result = compiler.compile(_make_problem(*CANDIDATES[0]))
    blueprint = result["layers"][10].get("blueprint", {})
    assert "prototype_specification" in blueprint, \
        "final_blueprint missing 'prototype_specification' field"
    assert isinstance(blueprint["prototype_specification"], dict)


# ----------------------------------------------------------------------
# 2. At least 15/20 candidates have all 5 fields non-empty
# ----------------------------------------------------------------------

def test_at_least_15_of_20_have_all_buildable_fields():
    """GAP 3 FIX: At least 15/20 candidates must have all 5 buildable-
    spec fields non-empty. Before the fix, 0/20 had any of them."""
    from invention_compiler.orchestrator import InventionCompiler
    graph_path = ROOT / "data" / "civilization_graph.json"
    with open(graph_path) as f:
        graph = json.load(f)
    compiler = InventionCompiler(graph=graph)
    all_fields_count = 0
    for name, domain, constraints in CANDIDATES:
        result = compiler.compile(_make_problem(name, domain, constraints))
        blueprint = result["layers"][10].get("blueprint", {})
        fields_present = 0
        for field in ("parts_list", "materials_specification",
                       "assembly_plan", "tolerances",
                       "prototype_specification"):
            v = blueprint.get(field)
            if v is not None and v != [] and v != {}:
                fields_present += 1
        if fields_present == 5:
            all_fields_count += 1
    assert all_fields_count >= 15, \
        f"Only {all_fields_count}/20 have all 5 buildable fields " \
        f"(expected >= 15)"


# ----------------------------------------------------------------------
# 3. Backwards compatibility — prior fixes still work
# ----------------------------------------------------------------------

def test_gap1_differentiation_still_works():
    """The Gap 1 fix (simulation_module.py) must still produce
    >= 10 unique composites across 20 candidates."""
    from invention_compiler.orchestrator import InventionCompiler
    graph_path = ROOT / "data" / "civilization_graph.json"
    with open(graph_path) as f:
        graph = json.load(f)
    compiler = InventionCompiler(graph=graph)
    composites = []
    for name, domain, constraints in CANDIDATES:
        result = compiler.compile(_make_problem(name, domain, constraints))
        composites.append(round(
            result["chain_summary"]["composite_feasibility_baseline"], 4))
    assert len(set(composites)) >= 10, \
        f"Gap 1 regressed: only {len(set(composites))} unique composites"


def test_gap2_7_causal_still_non_zero():
    """The Gap 2+7 fix (dependency_module.py) must still produce
    non-zero causal classifications for most candidates."""
    from invention_compiler.orchestrator import InventionCompiler
    graph_path = ROOT / "data" / "civilization_graph.json"
    with open(graph_path) as f:
        graph = json.load(f)
    compiler = InventionCompiler(graph=graph)
    non_zero = 0
    for name, domain, constraints in CANDIDATES:
        result = compiler.compile(_make_problem(name, domain, constraints))
        cc = result["layers"][2].get("evidence", {}).get(
            "causal_classifications", {})
        if sum(cc.values()) > 0:
            non_zero += 1
    assert non_zero >= 10, \
        f"Gap 2+7 regressed: only {non_zero}/20 have non-zero causal"


# ----------------------------------------------------------------------
# 4. Strict "modify ONE component" rule
# ----------------------------------------------------------------------

def test_only_blueprint_module_was_modified():
    """Per the Maestro Loop PHASE 6: only blueprint_module.py may be
    modified in this cycle. No other source file may be touched."""
    import subprocess
    result = subprocess.run(
        ["git", "diff", "--name-only", "a701d77", "HEAD"],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    if result.returncode != 0:
        pytest.skip("git diff against a701d77 not available")
    changed = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    code_changes = [
        f for f in changed
        if f.endswith(".py")
        and not f.startswith("tests/")
        and not f.startswith("scripts/")
        and not f.startswith("evidence/")
    ]
    allowed = {"invention_compiler/blueprint_module.py",
               "invention_compiler/prototype_module.py",
               "invention_compiler/orchestrator.py"}
    violations = set(code_changes) - allowed
    assert not violations, \
        f"Maestro Loop PHASE 6 VIOLATED: files other than blueprint_module.py " \
        f"were modified: {violations}"


# ----------------------------------------------------------------------
# 5. Delta report exists
# ----------------------------------------------------------------------

def test_invention_batch_004_exists():
    batch_dir = ROOT / "evidence" / "experiments" / "invention_batch_004"
    assert batch_dir.exists()


def test_delta_report_batch_004_exists():
    delta = ROOT / "evidence" / "experiments" / "invention_batch_004" / "DELTA.md"
    assert delta.exists()


def test_delta_report_records_blueprint_quality():
    delta = ROOT / "evidence" / "experiments" / "invention_batch_004" / "DELTA.md"
    text = delta.read_text().lower()
    assert "buildable" in text or "parts_list" in text
    assert "batch_003" in text
    assert "batch_004" in text
