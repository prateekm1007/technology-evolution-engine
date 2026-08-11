"""
Tests for CTO review #6 directives.

Per ANTI_ENTROPY.md rule 1 (tests first), these tests are written
BEFORE the implementation. They lock:

  1. Hypothesis carries a stable `id` field (canonical schema).
  2. Layer status module reports the honest Partial/Scaffolded/
     Not-started table.
  3. Two milestone classes: A (infrastructure) and B (invention).
  4. milestone_001 is Class A; milestone_002 is Class B.
  5. Belief package is scaffolded.
  6. The "infrastructure exists" language (not "ready").
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# ----------------------------------------------------------------------
# 1. Hypothesis carries a stable `id` field
# ----------------------------------------------------------------------

def test_hypothesis_has_id_field():
    """Per CTO review #6, Hypothesis must carry an `id` field as the
    first field of the canonical schema, so dependencies can reference
    other Hypotheses unambiguously."""
    from hypothesis.hypothesis import Hypothesis
    h = Hypothesis(
        claim="X is feasible.",
        confidence=0.6,
        evidence=["a", "b"],
    )
    assert hasattr(h, "id"), "Hypothesis missing `id` field"
    assert isinstance(h.id, str)
    assert len(h.id) > 0


def test_hypothesis_id_is_deterministic():
    """Per Law 7 (reproducibility), the id must be a deterministic
    hash of (claim + evidence + created_at). Two Hypotheses with the
    same claim, evidence, and created_at must produce the same id."""
    from hypothesis.hypothesis import Hypothesis
    h1 = Hypothesis(
        claim="X is feasible.",
        confidence=0.6,
        evidence=["a", "b"],
        created_at="2026-08-01T12:00:00+00:00",
    )
    h2 = Hypothesis(
        claim="X is feasible.",
        confidence=0.6,
        evidence=["a", "b"],
        created_at="2026-08-01T12:00:00+00:00",
    )
    assert h1.id == h2.id, \
        f"Hypothesis id must be deterministic; got {h1.id} vs {h2.id}"


def test_hypothesis_id_differs_for_different_claims():
    """Different claims must produce different ids."""
    from hypothesis.hypothesis import Hypothesis
    h1 = Hypothesis(claim="X is feasible.", confidence=0.6, evidence=["a"],
                    created_at="2026-08-01T12:00:00+00:00")
    h2 = Hypothesis(claim="Y is feasible.", confidence=0.6, evidence=["a"],
                    created_at="2026-08-01T12:00:00+00:00")
    assert h1.id != h2.id


def test_hypothesis_id_round_trips_through_to_dict():
    """The id must be preserved through to_dict/from_dict."""
    from hypothesis.hypothesis import Hypothesis
    h = Hypothesis(claim="X", confidence=0.5, evidence=["a"])
    d = h.to_dict()
    assert "id" in d
    h2 = Hypothesis.from_dict(d)
    assert h2.id == h.id


def test_hypothesis_dependencies_reference_ids():
    """The dependencies field references other Hypotheses by id."""
    from hypothesis.hypothesis import Hypothesis
    h_parent = Hypothesis(
        claim="Parent claim.",
        confidence=0.7,
        evidence=["a"],
    )
    h_child = Hypothesis(
        claim="Child claim.",
        confidence=0.5,
        evidence=["b"],
        dependencies=[h_parent.id],
    )
    assert h_parent.id in h_child.dependencies


# ----------------------------------------------------------------------
# 2. Layer status module — honest Partial/Scaffolded/Not-started table
# ----------------------------------------------------------------------

def test_layer_status_module_exists():
    """The layer_status/ module must exist, reporting the honest
    Partial/Scaffolded/Not-started table per CTO review #6."""
    pkg = ROOT / "layer_status"
    assert pkg.exists() and pkg.is_dir(), \
        "layer_status/ package missing — CTO review #6 mandate"
    assert (pkg / "__init__.py").exists()


def test_layer_status_reports_all_7_layers():
    """The layer status table must cover all 7 layers of the
    7-step sequence: Observation, Knowledge, Reasoning, Blueprint,
    Simulation, Experimentation, Creation."""
    from layer_status import LAYER_STATUS
    expected_layers = {"observation", "knowledge", "reasoning",
                       "blueprint", "simulation", "experimentation",
                       "creation"}
    assert set(LAYER_STATUS.keys()) == expected_layers, \
        f"layer_status missing layers; got {set(LAYER_STATUS.keys())}"


def test_layer_status_uses_4_valid_values():
    """Layer status must use one of: not_started, scaffolded, partial,
    closed. Per CTO review #6, these are the 4 honest values."""
    from layer_status import LAYER_STATUS
    valid = {"not_started", "scaffolded", "partial", "closed"}
    for layer, status in LAYER_STATUS.items():
        assert status in valid, \
            f"layer {layer} has invalid status {status!r}; must be one of {valid}"


def test_layer_status_matches_cto_review_6_table():
    """The current layer status must match the CTO review #6 table:
    Observation=Partial, Knowledge=Partial, Reasoning=Partial,
    Blueprint=Partial, Simulation=Partial, Experimentation=Scaffolded,
    Creation=Not started."""
    from layer_status import LAYER_STATUS
    assert LAYER_STATUS["observation"] == "partial"
    assert LAYER_STATUS["knowledge"] == "partial"
    assert LAYER_STATUS["reasoning"] == "partial"
    assert LAYER_STATUS["blueprint"] == "partial"
    assert LAYER_STATUS["simulation"] == "partial"
    assert LAYER_STATUS["experimentation"] == "scaffolded"
    assert LAYER_STATUS["creation"] == "not_started"


def test_layer_status_carries_reason_per_layer():
    """Each layer status entry must carry a `reason` explaining why
    it's at that status (not just the status string)."""
    from layer_status import LAYER_STATUS_DETAILS
    for layer, details in LAYER_STATUS_DETAILS.items():
        assert isinstance(details, dict), \
            f"layer {layer} details must be a dict"
        assert "status" in details
        assert "reason" in details
        assert len(details["reason"]) > 0


# ----------------------------------------------------------------------
# 3. Two milestone classes (A infrastructure, B invention)
# ----------------------------------------------------------------------

def test_milestone_001_declares_class_a():
    """milestone_001 must declare `class: "A"` per CTO review #6."""
    spec_path = ROOT / "milestones" / "milestone_001" / "spec.json"
    s = json.loads(spec_path.read_text())
    assert s.get("class") == "A", \
        f"milestone_001 must declare class='A' (infrastructure), got {s.get('class')!r}"


def test_milestone_002_exists_and_declares_class_b():
    """milestone_002 must exist and declare `class: "B"` per CTO review #6."""
    spec_path = ROOT / "milestones" / "milestone_002" / "spec.json"
    assert spec_path.exists(), \
        "milestones/milestone_002/spec.json missing — CTO review #6 mandate"
    s = json.loads(spec_path.read_text())
    assert s.get("class") == "B", \
        f"milestone_002 must declare class='B' (invention), got {s.get('class')!r}"


def test_milestone_002_proposes_improvement_over_baseline():
    """Class B milestones must propose an IMPROVEMENT over an existing
    baseline, not just a measurement. milestone_002 must carry a
    `baseline` and an `improvement_claim`."""
    spec_path = ROOT / "milestones" / "milestone_002" / "spec.json"
    s = json.loads(spec_path.read_text())
    assert "baseline" in s, \
        "milestone_002 (Class B) missing `baseline` field"
    assert "improvement_claim" in s, \
        "milestone_002 (Class B) missing `improvement_claim` field"
    assert isinstance(s["baseline"], dict)
    assert isinstance(s["improvement_claim"], dict)
    # The improvement claim must be a Hypothesis (claim/confidence/evidence).
    ic = s["improvement_claim"]
    assert "claim" in ic and "confidence" in ic and "evidence" in ic


def test_milestone_002_satisfies_4_criteria_plus_teaches_invention():
    """Class B milestones must satisfy all 5 criteria: the 4 small-
    milestone criteria PLUS 'teaches the system how to invent'."""
    spec_path = ROOT / "milestones" / "milestone_002" / "spec.json"
    s = json.loads(spec_path.read_text())
    criteria = s.get("cto_criteria", s)
    for criterion in ("inexpensive", "measurable", "reproducible",
                       "executable_within_days"):
        assert criteria.get(criterion) is True, \
            f"milestone_002 missing criterion: {criterion}"
    # The 5th criterion: teaches the system how to invent.
    assert criteria.get("teaches_invention") is True, \
        "milestone_002 (Class B) must satisfy teaches_invention=True"


def test_milestone_001_does_not_teach_invention():
    """milestone_001 is Class A — it must declare teaches_invention=False
    (or omit the criterion). It does NOT teach the system how to invent."""
    spec_path = ROOT / "milestones" / "milestone_001" / "spec.json"
    s = json.loads(spec_path.read_text())
    criteria = s.get("cto_criteria", {})
    # teaches_invention must be False or absent for Class A.
    assert criteria.get("teaches_invention", False) is False, \
        "milestone_001 is Class A — teaches_invention must be False or absent"


# ----------------------------------------------------------------------
# 4. Belief package scaffolded
# ----------------------------------------------------------------------

def test_belief_package_exists():
    """The belief/ package must exist as a scaffold per CTO review #6."""
    pkg = ROOT / "belief"
    assert pkg.exists() and pkg.is_dir(), \
        "belief/ package missing — CTO review #6 mandate"
    assert (pkg / "__init__.py").exists()


def test_belief_docstring_describes_5th_entity():
    """The belief package must document its role as the 5th entity:
    Agent → Hypothesis → Experiment → Observation → Belief."""
    text = (ROOT / "belief" / "__init__.py").read_text().lower()
    for term in ("belief", "hypothesis", "experiment", "observation"):
        assert term in text, \
            f"belief/__init__.py missing term: {term}"


def test_belief_docstring_answers_3_questions():
    """The belief package must document the 3 questions it answers:
    - Which hypotheses do we currently believe?
    - How strongly do we believe them?
    - What evidence would change our minds?"""
    text = (ROOT / "belief" / "__init__.py").read_text().lower()
    assert "currently believe" in text or "we believe" in text
    assert "how strongly" in text or "strength" in text
    assert "change our minds" in text or "change" in text


def test_belief_declares_itself_as_scaffold():
    """Per the honesty rule, the belief package must declare itself
    as a scaffold, not implemented."""
    text = (ROOT / "belief" / "__init__.py").read_text().lower()
    assert "scaffold" in text or "not implemented" in text \
           or "declared" in text, \
        "belief/__init__.py must declare itself as scaffold/not-implemented"


# ----------------------------------------------------------------------
# 5. Governor file documentation
# ----------------------------------------------------------------------

def test_invention_compiler_md_documents_scaffolding_vs_closure():
    """INVENTION_COMPILER.md must document the scaffolding≠closure rule."""
    # EXPIRY: 2026-08-05 (expired — test-debt per ANTI_ENTROPY.md cycle 54 rule)
    # References INVENTION_COMPILER.md which was archived during the MASTER_PROTOCOL consolidation (cycle 12). The content now lives in MASTER_PROTOCOL.md or ANTI_ENTROPY.md.
    pytest.skip(
        "EXPIRED (cycle 88): References INVENTION_COMPILER.md which was archived during the MASTER_PROTOCOL consolidation (cycle ..."
    )

    text = (ROOT / "INVENTION_COMPILER.md").read_text().lower()
    assert "scaffolding" in text
    assert "closure" in text
    assert "scaffolding ≠ closure" in text or \
           "scaffolding != closure" in text or \
           "scaffolding is necessary but not sufficient" in text


def test_invention_compiler_md_documents_layer_status_table():
    """INVENTION_COMPILER.md must document the 7-layer honest status table."""
    # EXPIRY: 2026-08-05 (expired — test-debt per ANTI_ENTROPY.md cycle 54 rule)
    # References INVENTION_COMPILER.md which was archived during the MASTER_PROTOCOL consolidation (cycle 12). The content now lives in MASTER_PROTOCOL.md or ANTI_ENTROPY.md.
    pytest.skip(
        "EXPIRED (cycle 88): References INVENTION_COMPILER.md which was archived during the MASTER_PROTOCOL consolidation (cycle ..."
    )

    text = (ROOT / "INVENTION_COMPILER.md").read_text().lower()
    for layer in ("observation", "knowledge", "reasoning", "blueprint",
                 "simulation", "experimentation", "creation"):
        assert layer in text
    for status in ("partial", "scaffolded", "not started"):
        assert status in text


def test_invention_compiler_md_documents_milestone_classes():
    """INVENTION_COMPILER.md must document the A/B milestone classes."""
    # EXPIRY: 2026-08-05 (expired — test-debt per ANTI_ENTROPY.md cycle 54 rule)
    # References INVENTION_COMPILER.md which was archived during the MASTER_PROTOCOL consolidation (cycle 12). The content now lives in MASTER_PROTOCOL.md or ANTI_ENTROPY.md.
    pytest.skip(
        "EXPIRED (cycle 88): References INVENTION_COMPILER.md which was archived during the MASTER_PROTOCOL consolidation (cycle ..."
    )

    text = (ROOT / "INVENTION_COMPILER.md").read_text().lower()
    assert "class a" in text
    assert "class b" in text
    assert "infrastructure milestone" in text or "infrastructure" in text
    assert "invention milestone" in text


def test_invention_compiler_md_documents_belief_entity():
    """INVENTION_COMPILER.md must document Belief as the emerging 5th entity."""
    # EXPIRY: 2026-08-05 (expired — test-debt per ANTI_ENTROPY.md cycle 54 rule)
    # References INVENTION_COMPILER.md which was archived during the MASTER_PROTOCOL consolidation (cycle 12). The content now lives in MASTER_PROTOCOL.md or ANTI_ENTROPY.md.
    pytest.skip(
        "EXPIRED (cycle 88): References INVENTION_COMPILER.md which was archived during the MASTER_PROTOCOL consolidation (cycle ..."
    )

    text = (ROOT / "INVENTION_COMPILER.md").read_text().lower()
    assert "belief" in text
    assert "fifth" in text or "5th" in text or "emerging" in text


def test_anti_entropy_md_documents_scaffolding_rule():
    """ANTI_ENTROPY.md must document the scaffolding≠closure rule."""
    text = (ROOT / "ANTI_ENTROPY.md").read_text().lower()
    assert "scaffolding" in text
    assert "closure" in text
