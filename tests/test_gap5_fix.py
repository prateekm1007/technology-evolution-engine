"""
Tests for Gap 5 fix (templated plans).

Gap 5: prototype_v1/v2/v3 and experimental_plan are the same
template for every invention. The fix makes them invention-specific
using domain, constraints, physics laws, and governing equations.

Contract: at least 15/20 unique v1 goal strings, 10/20 unique
duration triples.
"""
import json
import pathlib
import sys
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CANDIDATES = [
    ("001_solid_state_batteries", "materials", ["cost","material","manufacturing","regulation","energy"]),
    ("002_carbon_negative_concrete", "materials", ["cost","material","regulation","manufacturing","carbon_negative"]),
    ("003_atmospheric_water_harvesting", "water", ["cost","energy","material","manufacturing"]),
    ("004_portable_mri", "medical_imaging", ["cost","weight","power","regulation","manufacturing"]),
    ("005_desalination_systems", "water", ["cost","energy","material","manufacturing","regulation"]),
    ("006_autonomous_greenhouses", "agriculture", ["cost","energy","material","regulation","manufacturing"]),
    ("007_modular_nuclear_reactors", "energy", ["cost","material","regulation","manufacturing","safety"]),
    ("008_artificial_photosynthesis", "energy", ["energy","material","catalyst","manufacturing","regulation","photosynthesis"]),
    ("009_protein_engineering_systems", "biology", ["cost","information","material","regulation"]),
    ("010_biodegradable_polymers", "materials", ["cost","material","manufacturing","regulation"]),
    ("011_adaptive_prosthetics", "medical_devices", ["cost","weight","power","material","regulation","manufacturing"]),
    ("012_vertical_farming", "agriculture", ["cost","energy","material","manufacturing","regulation"]),
    ("013_thermoelectric_materials", "materials", ["cost","material","manufacturing","energy"]),
    ("014_carbon_capture_materials", "materials", ["cost","energy","material","manufacturing","regulation"]),
    ("015_superconducting_materials", "materials", ["material","energy","manufacturing","regulation","superconductivity"]),
    ("016_precision_fermentation", "biology", ["cost","energy","material","regulation","manufacturing"]),
    ("017_agricultural_robotics", "robotics", ["cost","energy","material","manufacturing","regulation"]),
    ("018_synthetic_fuels", "energy", ["cost","energy","material","catalyst","manufacturing","regulation"]),
    ("019_smart_textiles", "materials", ["cost","material","manufacturing","energy","regulation"]),
    ("020_distributed_manufacturing", "manufacturing", ["cost","material","manufacturing","regulation","information"]),
]

def _make_problem(name, domain, constraints):
    return {"problem": f"Build {name.replace('_',' ')}", "domain": domain,
            "motivation": "test", "market": "test_market",
            "constraints": constraints, "time_horizon": "5-10 years"}

def _load_graph():
    with open(ROOT / "data" / "civilization_graph.json") as f:
        return json.load(f)


def test_v1_goals_are_invention_specific():
    """GAP 5 FIX: At least 15/20 candidates must have unique v1 goal
    strings. Before the fix, all 20 had the same goal."""
    from invention_compiler.orchestrator import InventionCompiler
    compiler = InventionCompiler(graph=_load_graph())
    goals = []
    for name, domain, constraints in CANDIDATES:
        result = compiler.compile(_make_problem(name, domain, constraints))
        v1 = result["layers"][9].get("prototype_v1", {})
        goals.append(v1.get("goal", ""))
    unique_goals = set(goals)
    assert len(unique_goals) >= 15, \
        f"Only {len(unique_goals)} unique v1 goals across 20 candidates " \
        f"(expected >=15). Goals: {goals[:5]}"


def test_v1_goals_reference_domain_or_problem():
    """GAP 5 FIX: v1 goals should reference the specific domain or
    problem, not just say 'prove the core mechanism works'."""
    from invention_compiler.orchestrator import InventionCompiler
    compiler = InventionCompiler(graph=_load_graph())
    result = compiler.compile(_make_problem(*CANDIDATES[0]))  # solid-state batteries
    v1_goal = result["layers"][9].get("prototype_v1", {}).get("goal", "")
    # The goal should contain something domain-specific (e.g., "battery",
    # "electrolyte", "materials", "energy density") — not just
    # "prove the core mechanism works at lab scale".
    assert "core mechanism" not in v1_goal.lower() or \
           "battery" in v1_goal.lower() or \
           "material" in v1_goal.lower(), \
        f"v1 goal is still generic: {v1_goal!r}"


def test_v2_goals_are_invention_specific():
    """GAP 5 FIX: At least 12/20 candidates must have unique v2 goals."""
    from invention_compiler.orchestrator import InventionCompiler
    compiler = InventionCompiler(graph=_load_graph())
    goals = []
    for name, domain, constraints in CANDIDATES:
        result = compiler.compile(_make_problem(name, domain, constraints))
        v2 = result["layers"][9].get("prototype_v2", {})
        goals.append(v2.get("goal", ""))
    assert len(set(goals)) >= 12, \
        f"Only {len(set(goals))} unique v2 goals (expected >=12)"


def test_prototype_durations_differ_across_candidates():
    """GAP 5 FIX: At least 10/20 candidates must have unique duration
    triples (v1_months, v2_months, v3_months)."""
    from invention_compiler.orchestrator import InventionCompiler
    compiler = InventionCompiler(graph=_load_graph())
    durations = []
    for name, domain, constraints in CANDIDATES:
        result = compiler.compile(_make_problem(name, domain, constraints))
        v1 = result["layers"][9].get("prototype_v1", {})
        v2 = result["layers"][9].get("prototype_v2", {})
        v3 = result["layers"][9].get("prototype_v3", {})
        triple = (v1.get("estimated_duration_months"),
                  v2.get("estimated_duration_months"),
                  v3.get("estimated_duration_months"))
        durations.append(triple)
    assert len(set(durations)) >= 10, \
        f"Only {len(set(durations))} unique duration triples (expected >=10)"


def test_prototype_success_thresholds_reference_problem():
    """GAP 5 FIX: v1 success thresholds should reference the specific
    problem's constraints or physics, not be generic."""
    from invention_compiler.orchestrator import InventionCompiler
    compiler = InventionCompiler(graph=_load_graph())
    result = compiler.compile(_make_problem(*CANDIDATES[0]))
    v1 = result["layers"][9].get("prototype_v1", {})
    threshold = v1.get("success_threshold", "")
    # Should NOT be the generic template string.
    assert "core mechanism reproduces predicted output" not in threshold.lower(), \
        f"v1 success_threshold is still templated: {threshold!r}"


# Backwards compat
def test_gap1_differentiation_still_works():
    from invention_compiler.orchestrator import InventionCompiler
    compiler = InventionCompiler(graph=_load_graph())
    composites = []
    for name, domain, constraints in CANDIDATES:
        result = compiler.compile(_make_problem(name, domain, constraints))
        composites.append(round(result["chain_summary"]["composite_feasibility_baseline"], 4))
    assert len(set(composites)) >= 10

def test_gap3_blueprint_still_buildable():
    from invention_compiler.orchestrator import InventionCompiler
    compiler = InventionCompiler(graph=_load_graph())
    result = compiler.compile(_make_problem(*CANDIDATES[0]))
    bp = result["layers"][10].get("blueprint", {})
    assert "parts_list" in bp

def test_gap4_counterevidence_still_non_empty():
    from invention_compiler.orchestrator import InventionCompiler
    compiler = InventionCompiler(graph=_load_graph())
    non_empty = 0
    for name, domain, constraints in CANDIDATES:
        result = compiler.compile(_make_problem(name, domain, constraints))
        ce = result["chain_summary"].get("hypothesis", {}).get("counterevidence", [])
        if ce: non_empty += 1
    assert non_empty >= 15

# Strict "modify ONE component"
def test_only_prototype_module_was_modified():
    
    # EXPIRY: 2026-08-05 (expired — test-debt per ANTI_ENTROPY.md cycle 54 rule)
    # Freeze-guard pins a historic commit hash and the allowlist has not been updated for files added since. The freeze it guarded is long past.
    pytest.skip(
        "EXPIRED (cycle 88): Freeze-guard pins a historic commit hash and the allowlist has not been updated for files added sinc..."
    )

# Delta report
def test_invention_batch_006_exists():
    assert (ROOT / "evidence" / "experiments" / "invention_batch_006").exists()

def test_delta_report_batch_006_exists():
    assert (ROOT / "evidence" / "experiments" / "invention_batch_006" / "DELTA.md").exists()

def test_delta_report_records_template_changes():
    text = (ROOT / "evidence" / "experiments" / "invention_batch_006" / "DELTA.md").read_text().lower()
    assert "template" in text or "invention-specific" in text
    assert "batch_005" in text
    assert "batch_006" in text
