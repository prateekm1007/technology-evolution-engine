"""
Tests for CTO review #5 directives.

Per ANTI_ENTROPY.md rule 1 (tests first), these tests are written
BEFORE the implementation. They lock:

  1. Loop 2 (resurrection) is partially_closed, NOT closed.
  2. Loop status can be one of: open, partially_closed, closed.
  3. The Hypothesis object carries the extended schema:
     counterevidence, assumptions, dependencies, created_at, updated_at.
  4. The agent/ package is scaffolded.
  5. The milestones/ package exists with milestone_001 satisfying the
     4 small-milestone criteria.
  6. The honest-claim rule: counterevidence is non-empty when applicable.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# ----------------------------------------------------------------------
# 1. Loop 2 reclassification to partially_closed
# ----------------------------------------------------------------------

def test_loop2_resurrection_is_partially_closed():
    """Per CTO review #5, Loop 2 (resurrection) must be
    partially_closed, NOT closed. The system has counterfactuals but
    has not demonstrated a real-world resurrection."""
    from loops.resurrection_loop import ResurrectionLoop
    s = ResurrectionLoop().status()
    assert s["closed"] is False, \
        f"Loop 2 should not be 'closed' — per CTO review #5 it is partially_closed"
    assert s.get("partially_closed") is True, \
        f"Loop 2 should set partially_closed=True — per CTO review #5"
    assert "partially_closed" in s.get("reason", "").lower() \
           or "partially" in s.get("reason", "").lower(), \
        f"Loop 2 reason must mention partially_closed: {s.get('reason')}"


def test_loop1_reconstruction_still_closed():
    """Loop 1 (reconstruction) stays closed — historical failures are
    observed facts, not predictions."""
    from loops.reconstruction_loop import ReconstructionLoop
    s = ReconstructionLoop().status()
    assert s["closed"] is True


def test_loop_status_can_be_partially_closed():
    """The loop status dict must support partially_closed as a value
    distinct from closed and open."""
    # We test by checking Loop 2 has partially_closed=True and closed=False,
    # and Loop 3 has both False (open).
    from loops.resurrection_loop import ResurrectionLoop
    from loops.forecasting_loop import ForecastingLoop
    s2 = ResurrectionLoop().status()
    s3 = ForecastingLoop().status()
    assert s2.get("partially_closed") is True
    assert s2["closed"] is False
    assert s3.get("partially_closed") is False
    assert s3["closed"] is False


# ----------------------------------------------------------------------
# 2. Extended Hypothesis schema
# ----------------------------------------------------------------------

def test_hypothesis_carries_counterevidence_field():
    """Per CTO review #5, Hypothesis must carry a `counterevidence`
    field — named inputs that would weaken the claim."""
    from hypothesis.hypothesis import Hypothesis
    h = Hypothesis(
        claim="X is feasible.",
        confidence=0.6,
        evidence=["a", "b"],
        counterevidence=["c", "d"],
    )
    assert h.counterevidence == ["c", "d"]


def test_hypothesis_counterevidence_defaults_to_empty_list():
    """counterevidence defaults to an empty list (no counter-signals).
    That's valid — the claim has no known counter-evidence."""
    from hypothesis.hypothesis import Hypothesis
    h = Hypothesis(claim="X", confidence=0.5, evidence=["a"])
    assert h.counterevidence == []


def test_hypothesis_carries_assumptions_field():
    """Per CTO review #5, Hypothesis must carry an `assumptions`
    field — preconditions the claim makes."""
    from hypothesis.hypothesis import Hypothesis
    h = Hypothesis(
        claim="X is feasible.",
        confidence=0.6,
        evidence=["a"],
        assumptions=["regulatory pathway is FDA 510(k)",
                     "permanent magnet field strength sufficient"],
    )
    assert len(h.assumptions) == 2


def test_hypothesis_carries_dependencies_field():
    """Per CTO review #5, Hypothesis must carry a `dependencies`
    field — IDs of other Hypotheses this one depends on."""
    from hypothesis.hypothesis import Hypothesis
    h = Hypothesis(
        claim="X is feasible.",
        confidence=0.6,
        evidence=["a"],
        dependencies=["hypothesis_battery_density_001"],
    )
    assert "hypothesis_battery_density_001" in h.dependencies


def test_hypothesis_carries_created_at_and_updated_at():
    """Per CTO review #5, Hypothesis must carry created_at and
    updated_at timestamps. updated_at is updated on reconcile()."""
    from hypothesis.hypothesis import Hypothesis
    import time
    h = Hypothesis(claim="X", confidence=0.5, evidence=["a"])
    assert h.created_at is not None
    assert h.updated_at is not None
    first_updated = h.updated_at
    # Reconcile after a small delay to verify updated_at changes.
    time.sleep(0.01)
    h.reconcile(outcome="pass", observation="X was observed")
    assert h.updated_at != first_updated, \
        "updated_at must change on reconcile()"


def test_hypothesis_extended_schema_round_trips():
    """The extended Hypothesis must round-trip through to_dict/from_dict."""
    from hypothesis.hypothesis import Hypothesis
    h = Hypothesis(
        claim="X is feasible.",
        confidence=0.62,
        evidence=["Ampere_law", "Maxwell_equations"],
        counterevidence=["superconducting_materials_shortage"],
        assumptions=["regulatory pathway is FDA 510(k)"],
        dependencies=["hypothesis_battery_001"],
    )
    d = h.to_dict()
    s = json.dumps(d)
    parsed = json.loads(s)
    assert parsed["counterevidence"] == ["superconducting_materials_shortage"]
    assert parsed["assumptions"] == ["regulatory pathway is FDA 510(k)"]
    assert parsed["dependencies"] == ["hypothesis_battery_001"]
    assert "created_at" in parsed
    assert "updated_at" in parsed


def test_hypothesis_backwards_compat_with_old_schema():
    """Old code that constructs Hypothesis without the new fields
    must still work — defaults are applied."""
    from hypothesis.hypothesis import Hypothesis
    # Old-style construction (no counterevidence/assumptions/dependencies).
    h = Hypothesis(claim="X", confidence=0.5, evidence=["a"])
    assert h.counterevidence == []
    assert h.assumptions == []
    assert h.dependencies == []
    assert h.status == "pending"


# ----------------------------------------------------------------------
# 3. Agent layer scaffold
# ----------------------------------------------------------------------

def test_agent_package_exists():
    """The agent/ package must exist as a scaffold per CTO review #5."""
    pkg = ROOT / "agent"
    assert pkg.exists() and pkg.is_dir(), \
        "agent/ package missing — CTO review #5 mandate"
    assert (pkg / "__init__.py").exists()


def test_agent_docstring_describes_evolution_loop():
    """The agent package must document the
    agent→hypothesis→experiment→observation→hypothesis loop."""
    text = (ROOT / "agent" / "__init__.py").read_text().lower()
    for term in ("agent", "hypothesis", "experiment", "observation"):
        assert term in text, \
            f"agent/__init__.py missing evolution-loop term: {term}"


def test_agent_declares_itself_as_scaffold():
    """Per the honesty rule, the agent package must declare itself
    as a scaffold, not implemented."""
    text = (ROOT / "agent" / "__init__.py").read_text().lower()
    assert "scaffold" in text or "not implemented" in text \
           or "declared" in text, \
        "agent/__init__.py must declare itself as scaffold/not-implemented"


# ----------------------------------------------------------------------
# 4. First small milestone
# ----------------------------------------------------------------------

def test_milestones_package_exists():
    """The milestones/ package must exist with milestone_001."""
    pkg = ROOT / "milestones"
    assert pkg.exists() and pkg.is_dir(), \
        "milestones/ package missing — CTO review #5 mandate"
    assert (pkg / "milestone_001").exists(), \
        "milestones/milestone_001/ missing"


def test_milestone_001_satisfies_4_criteria():
    """Milestone 001 must declare that it satisfies the 4 CTO criteria:
    inexpensive, measurable, reproducible, executable within days.
    The criteria may be at the top level or nested under cto_criteria."""
    m_dir = ROOT / "milestones" / "milestone_001"
    spec = m_dir / "spec.json"
    assert spec.exists(), "milestones/milestone_001/spec.json missing"
    s = json.loads(spec.read_text())
    # Accept either top-level or nested under cto_criteria.
    criteria = s.get("cto_criteria", s)
    for criterion in ("inexpensive", "measurable", "reproducible",
                       "executable_within_days"):
        assert criterion in criteria, \
            f"milestone_001 spec missing criterion: {criterion}"
        assert criteria[criterion] is True, \
            f"milestone_001 criterion {criterion} must be True"


def test_milestone_001_has_prediction_and_measurement_plan():
    """Milestone 001 must carry a prediction (a Hypothesis) and a
    measurement plan (what numeric value will be measured)."""
    m_dir = ROOT / "milestones" / "milestone_001"
    spec = json.loads((m_dir / "spec.json").read_text())
    assert "prediction" in spec, \
        "milestone_001 spec must carry a prediction (Hypothesis)"
    assert "measurement_plan" in spec, \
        "milestone_001 spec must carry a measurement plan"
    pred = spec["prediction"]
    assert "claim" in pred and "confidence" in pred \
           and "evidence" in pred, \
        "milestone_001 prediction must be a Hypothesis (claim/confidence/evidence)"


def test_milestone_001_under_30_days_and_1000_dollars():
    """Per ANTI_ENTROPY.md: no milestone may require >30 days or >$1000."""
    m_dir = ROOT / "milestones" / "milestone_001"
    spec = json.loads((m_dir / "spec.json").read_text())
    assert spec.get("estimated_days", 999) <= 30, \
        f"milestone_001 estimated_days={spec.get('estimated_days')} > 30"
    assert spec.get("estimated_cost_usd", 9999) <= 1000, \
        f"milestone_001 estimated_cost_usd={spec.get('estimated_cost_usd')} > 1000"


def test_milestone_001_status_is_open():
    """Milestone 001 must honestly declare status='open' — it has not
    been executed yet."""
    m_dir = ROOT / "milestones" / "milestone_001"
    spec = json.loads((m_dir / "spec.json").read_text())
    assert spec.get("status") == "open", \
        f"milestone_001 status must be 'open' (not yet executed), got {spec.get('status')}"


# ----------------------------------------------------------------------
# 5. Governor file documentation
# ----------------------------------------------------------------------

def test_invention_compiler_md_documents_partially_closed():
    """INVENTION_COMPILER.md must document the partially_closed state."""
    text = (ROOT / "INVENTION_COMPILER.md").read_text().lower()
    assert "partially_closed" in text, \
        "INVENTION_COMPILER.md missing partially_closed discussion"


def test_invention_compiler_md_documents_extended_hypothesis_schema():
    """INVENTION_COMPILER.md must document the extended Hypothesis schema
    (counterevidence, assumptions, dependencies, created_at, updated_at)."""
    text = (ROOT / "INVENTION_COMPILER.md").read_text().lower()
    for field in ("counterevidence", "assumptions", "dependencies",
                   "created_at", "updated_at"):
        assert field in text, \
            f"INVENTION_COMPILER.md missing extended Hypothesis field: {field}"


def test_invention_compiler_md_documents_agent_loop():
    """INVENTION_COMPILER.md must document the
    agent→hypothesis→experiment→observation→hypothesis loop."""
    text = (ROOT / "INVENTION_COMPILER.md").read_text().lower()
    for term in ("agent", "experiment", "observation"):
        assert term in text, \
            f"INVENTION_COMPILER.md missing agent-loop term: {term}"


def test_invention_compiler_md_documents_small_milestone_rule():
    """INVENTION_COMPILER.md must document the small-milestone rule
    (inexpensive, measurable, reproducible, days)."""
    text = (ROOT / "INVENTION_COMPILER.md").read_text().lower()
    for term in ("inexpensive", "measurable", "reproducible",
                 "executable within days"):
        assert term in text, \
            f"INVENTION_COMPILER.md missing small-milestone criterion: {term}"


def test_anti_entropy_md_documents_partially_closed_rule():
    """ANTI_ENTROPY.md must document the partially_closed ≠ closed rule."""
    text = (ROOT / "ANTI_ENTROPY.md").read_text().lower()
    assert "partially_closed" in text
    assert "partially_closed ≠ closed" in text or \
           "partially_closed != closed" in text or \
           "three possible states" in text
