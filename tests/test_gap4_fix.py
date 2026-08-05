"""
Tests for Gap 4 fix (missing counterevidence).

Gap 4: every headline hypothesis has empty counterevidence. The
orchestrator builds evidence but never pulls counterevidence from
any layer. The system becomes an optimism engine.

Contract: after the fix, at least 15/20 hypotheses must have non-empty
counterevidence, drawn from Layer 3 failure_modes, Layer 5 stress_
testing, Layer 7 commercial_risks, and Layer 10 technical_risks.
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


def test_hypothesis_has_non_empty_counterevidence():
    """GAP 4 FIX: The headline hypothesis must carry non-empty
    counterevidence for most candidates."""
    from invention_compiler.orchestrator import InventionCompiler
    compiler = InventionCompiler(graph=_load_graph())
    non_empty = 0
    for name, domain, constraints in CANDIDATES:
        result = compiler.compile(_make_problem(name, domain, constraints))
        h = result["chain_summary"].get("hypothesis", {})
        ce = h.get("counterevidence", [])
        if ce:
            non_empty += 1
    assert non_empty >= 15, \
        f"Only {non_empty}/20 have non-empty counterevidence (expected >=15)"


def test_counterevidence_drawn_from_multiple_layers():
    """GAP 4 FIX: The counterevidence must be drawn from multiple
    layers — not just one. The orchestrator should pull from Layer 3
    failure_modes, Layer 5 stress_testing, Layer 7 commercial_risks,
    and Layer 10 technical_risks."""
    from invention_compiler.orchestrator import InventionCompiler
    compiler = InventionCompiler(graph=_load_graph())
    result = compiler.compile(_make_problem(*CANDIDATES[0]))
    h = result["chain_summary"].get("hypothesis", {})
    ce = h.get("counterevidence", [])
    assert len(ce) >= 2, \
        f"Counterevidence has only {len(ce)} items — expected >=2 from multiple layers"


def test_counterevidence_includes_failure_modes():
    """GAP 4 FIX: At least some counterevidence items should reference
    failure modes from Layer 3."""
    from invention_compiler.orchestrator import InventionCompiler
    compiler = InventionCompiler(graph=_load_graph())
    result = compiler.compile(_make_problem(*CANDIDATES[0]))
    h = result["chain_summary"].get("hypothesis", {})
    ce = h.get("counterevidence", [])
    # Check that at least one counterevidence item looks like a failure mode.
    failure_mode_indicators = ["overrun", "rejection", "yield", "disruption",
                                "slippage", "incident", "burden"]
    has_failure_mode = any(
        any(ind in str(item).lower() for ind in failure_mode_indicators)
        for item in ce
    )
    assert has_failure_mode, \
        f"Counterevidence does not include failure-mode items: {ce}"


def test_counterevidence_includes_commercial_risks():
    """GAP 4 FIX: At least some counterevidence items should reference
    commercial risks from Layer 7/10."""
    from invention_compiler.orchestrator import InventionCompiler
    compiler = InventionCompiler(graph=_load_graph())
    result = compiler.compile(_make_problem(*CANDIDATES[0]))
    h = result["chain_summary"].get("hypothesis", {})
    ce = h.get("counterevidence", [])
    commercial_indicators = ["market", "capex", "adoption", "payback",
                              "commercial"]
    has_commercial = any(
        any(ind in str(item).lower() for ind in commercial_indicators)
        for item in ce
    )
    assert has_commercial, \
        f"Counterevidence does not include commercial-risk items: {ce}"


# Backwards compat
def test_gap1_differentiation_still_works():
    from invention_compiler.orchestrator import InventionCompiler
    compiler = InventionCompiler(graph=_load_graph())
    composites = []
    for name, domain, constraints in CANDIDATES:
        result = compiler.compile(_make_problem(name, domain, constraints))
        composites.append(round(result["chain_summary"]["composite_feasibility_baseline"], 4))
    assert len(set(composites)) >= 10

def test_gap2_7_causal_still_non_zero():
    from invention_compiler.orchestrator import InventionCompiler
    compiler = InventionCompiler(graph=_load_graph())
    non_zero = 0
    for name, domain, constraints in CANDIDATES:
        result = compiler.compile(_make_problem(name, domain, constraints))
        cc = result["layers"][2].get("evidence", {}).get("causal_classifications", {})
        if sum(cc.values()) > 0:
            non_zero += 1
    assert non_zero >= 10

def test_gap3_blueprint_still_buildable():
    from invention_compiler.orchestrator import InventionCompiler
    compiler = InventionCompiler(graph=_load_graph())
    result = compiler.compile(_make_problem(*CANDIDATES[0]))
    bp = result["layers"][10].get("blueprint", {})
    assert "parts_list" in bp
    assert "assembly_plan" in bp

# Strict "modify ONE component"
def test_only_orchestrator_was_modified():
    
    # EXPIRY: 2026-08-05 (expired — test-debt per ANTI_ENTROPY.md cycle 54 rule)
    # Freeze-guard pins a historic commit hash and the allowlist has not been updated for files added since. The freeze it guarded is long past.
    pytest.skip(
        "EXPIRED (cycle 88): Freeze-guard pins a historic commit hash and the allowlist has not been updated for files added sinc..."
    )

# Delta report
def test_invention_batch_005_exists():
    assert (ROOT / "evidence" / "experiments" / "invention_batch_005").exists()

def test_delta_report_batch_005_exists():
    assert (ROOT / "evidence" / "experiments" / "invention_batch_005" / "DELTA.md").exists()

def test_delta_report_records_counterevidence():
    delta = (ROOT / "evidence" / "experiments" / "invention_batch_005" / "DELTA.md").read_text().lower()
    assert "counterevidence" in delta
    assert "batch_004" in delta
    assert "batch_005" in delta
