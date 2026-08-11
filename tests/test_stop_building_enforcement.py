"""
test_stop_building_enforcement.py — Cycle 258 STOP BUILDING list enforcement.

Per ROADMAP_V2.md and STOP_BUILDING.md, the following work is FORBIDDEN
until Programs A-D are complete (Gate 1 + Gate 2 + Gate 3 + Gate 4 = PASS):

  1. Better Proposal Composer (beyond Gen0 experiments)
  2. New discovery algorithms
  3. New invention algorithms
  4. L6 search
  5. Product features
  6. UI improvements
  7. Commercialization work
  8. Benchmark tuning
  9. Score improvements

This test enforces the list by scanning the repository for forbidden
patterns. It fails CI if any forbidden work is detected.

The test is intentionally conservative — it scans for clear violations,
not subtle ones. False positives are preferred over false negatives
(we'd rather block legitimate work than allow forbidden work).
"""
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


# ============================================================================
# FORBIDDEN PATTERNS
# ============================================================================

# Patterns that indicate forbidden work. Each pattern is a regex.
# The test scans .py files in source directories for these patterns.
#
# NOTE: These patterns are deliberately narrow. They look for NEW work
# that violates the STOP BUILDING list, not existing work that predates
# the list (which is documented in FAILURES.md).

FORBIDDEN_PATTERNS = [
    # 1. Better Proposal Composer (beyond Gen0 experiments)
    #    Pattern: new file or class claiming to be a ProposalComposer
    #    beyond Gen0. The existing dr92_proposal_composer.py is Gen0
    #    and is FROZEN.
    (
        r"class\s+ProposalComposerGen[1-9]",
        "Forbidden: Proposal Composer generation beyond Gen0. "
        "Stage P1 requires Gate 1 (Measurement) PASS first."
    ),
    (
        r"class\s+MechanismDrivenProposalComposer",
        "Forbidden: Mechanism-driven Proposal Composer. "
        "Stage P1 requires Gate 1 (Measurement) PASS first."
    ),

    # 4. L6 search
    #    Pattern: new L6 search operators
    (
        r"class\s+L6[A-Z]",
        "Forbidden: L6 search. L1-L5 research is complete per Program F. "
        "L6 is a closed research direction."
    ),
    (
        r"def\s+l6_\w+",
        "Forbidden: L6 search function. L1-L5 research is complete per Program F."
    ),

    # 8. Benchmark tuning (loosening thresholds to make scores look better)
    #    Pattern: comments that explicitly say "loosen threshold to pass test"
    #    or "relax threshold to make X pass". We DO NOT match every
    #    "lower threshold" because legitimate code uses that phrase
    #    (e.g. min_triple_frequency=1 is a real parameter, not benchmark tuning).
    (
        r"#\s*loosen\s+(?:threshold|criteria)\s+to\s+(?:pass|make)",
        "Forbidden: benchmark tuning (loosening thresholds to pass tests). "
        "This is the No-Gaming Rule violation (CONSTITUTION.md)."
    ),
    (
        r"#\s*relax\s+(?:threshold|criteria)\s+to\s+(?:pass|make)",
        "Forbidden: benchmark tuning (relaxing thresholds to pass tests). "
        "This is the No-Gaming Rule violation (CONSTITUTION.md)."
    ),
    (
        r"#\s*lower\s+(?:threshold|criteria)\s+to\s+(?:pass|make)",
        "Forbidden: benchmark tuning (lowering thresholds to pass tests). "
        "This is the No-Gaming Rule violation (CONSTITUTION.md)."
    ),

    # 9. Score improvements without measurement improvements
    #    Pattern: commits that improve scores without touching measurement
    #    (this is hard to detect mechanically; we look for the most
    #    egregious case: comments claiming score improvements)
    (
        r"#\s*improved\s+(?:F1|score|accuracy)\s+(?:from|by)",
        "Forbidden: score improvement without measurement improvement. "
        "Principle 1 (CONSTITUTION.md): no capability work until "
        "measurement layer proves it can measure that capability."
    ),
]


# Directories to scan for forbidden patterns
SCAN_DIRECTORIES = [
    "audit",
    "benchmarks",
    "product",
    "scripts",
    "invention_compiler",
    "agent",
    "web",
]

# Directories to EXCLUDE from scanning (existing frozen work)
EXCLUDE_PATHS = {
    # Gen0 ProposalComposer is FROZEN, not forbidden
    "audit/measurement_integrity/dr92_proposal_composer.py",
    "tests/test_dr92_proposal_composer.py",
    # Existing L5b synthesis is FROZEN, not forbidden
    "scripts/l5b_synthesis.py",
    "scripts/l5b_synthesis_multiseed.py",
    "scripts/meta_invention.py",
}


def _is_excluded(path: Path) -> bool:
    """Check if a file path is in the exclude list."""
    try:
        rel = path.relative_to(REPO)
        rel_str = str(rel)
    except ValueError:
        return True
    # Exclude tests directory (test files can mention forbidden patterns
    # in their assertions)
    if rel_str.startswith("tests/"):
        return True
    # Exclude the stop building enforcement test itself
    if "test_stop_building" in rel_str:
        return True
    # Exclude the roadmap / stop_building docs themselves (they mention
    # the forbidden patterns)
    if rel_str in ("STOP_BUILDING.md", "ROADMAP_V2.md", "GO_NO_GO_GATES.md"):
        return True
    if rel_str.startswith("programs/"):
        return True
    # Explicit excludes
    return rel_str in EXCLUDE_PATHS


def _scan_file_for_forbidden_patterns(path: Path) -> list:
    """Scan a Python file for forbidden patterns. Return list of (line_no, pattern, message)."""
    if _is_excluded(path):
        return []
    if not path.exists():
        return []
    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, IsADirectoryError):
        return []

    violations = []
    for line_no, line in enumerate(content.splitlines(), start=1):
        for pattern, message in FORBIDDEN_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                violations.append((line_no, pattern, message, line.strip()))
    return violations


# ============================================================================
# TESTS
# ============================================================================

def test_roadmap_v2_exists():
    """ROADMAP_V2.md must exist as the canonical project plan."""
    assert (REPO / "ROADMAP_V2.md").exists(), (
        "ROADMAP_V2.md must exist as the canonical project plan (cycle 258)."
    )


def test_stop_building_md_exists():
    """STOP_BUILDING.md must exist as the enforceable forbidden list."""
    assert (REPO / "STOP_BUILDING.md").exists()


def test_go_no_go_gates_md_exists():
    """GO_NO_GO_GATES.md must exist as the canonical gate structure."""
    assert (REPO / "GO_NO_GO_GATES.md").exists()


def test_constitution_references_principle_1():
    """CONSTITUTION.md must reference Principle 1 (measurement-first)."""
    constitution = (REPO / "CONSTITUTION.md").read_text()
    assert "Principle 1" in constitution
    assert "ROADMAP_V2.md" in constitution
    assert "STOP_BUILDING" in constitution


def test_contributing_has_stop_building_check():
    """CONTRIBUTING.md must have the STOP BUILDING pre-commit check."""
    contributing = (REPO / "CONTRIBUTING.md").read_text()
    assert "STOP BUILDING check" in contributing
    assert "Program A, B, C, or D" in contributing


def test_measurement_engine_specification_exists():
    """Stage M1 deliverable: MeasurementEngineSpecification.md must exist."""
    spec_path = REPO / "programs" / "A_metrology" / "MeasurementEngineSpecification.md"
    assert spec_path.exists()


def test_measurement_specification_has_required_fields():
    """Each SPECIFIED metric in the spec must have all 9 required fields.

    TODO metrics (those marked "TODO" in the Status column) are exempt
    — they are placeholders for future specification work.
    """
    spec_path = REPO / "programs" / "A_metrology" / "MeasurementEngineSpecification.md"
    spec = spec_path.read_text()
    required_fields = [
        "**Inputs:**",
        "**Outputs:**",
        "**Assumptions:**",
        "**Known failure modes:**",
        "**Uncertainty:**",
        "**Evidence tier:**",
        "**Calibration status:**",
        "**Owner:**",
        "**Acceptance:**",
    ]
    # Count specified metrics (those with "**Inputs:**")
    n_specified = spec.count("**Inputs:**")
    # Each specified metric should have all 9 fields
    for field in required_fields:
        n_field = spec.count(field)
        assert n_field == n_specified, (
            f"Field {field!r} appears {n_field} times but should appear "
            f"{n_specified} times (once per specified metric). "
            f"Either add the field to all specified metrics, or mark "
            f"the metric as TODO in the inventory table."
        )
    # Stage M1 requires all 30 metrics specified (cycle 260: complete)
    assert n_specified >= 30, (
        f"Stage M1 requires at least 30 specified metrics, found {n_specified}"
    )


def test_invention_metrics_m101_through_m105_specified():
    """Cycle 260: M-101 through M-105 (invention metrics) must be specified."""
    spec_path = REPO / "programs" / "A_metrology" / "MeasurementEngineSpecification.md"
    spec = spec_path.read_text()
    for metric_id in ("M-101", "M-102", "M-103", "M-104", "M-105"):
        # Each should have a section header
        assert f"## {metric_id}:" in spec, (
            f"Missing section header for {metric_id}"
        )
        # Each should be marked SPECIFIED in the inventory, not TODO
        # (find the inventory row for this metric)
        for line in spec.splitlines():
            if line.startswith(f"| {metric_id} "):
                assert "TODO" not in line, (
                    f"{metric_id} still marked TODO in inventory: {line}"
                )
                assert "SPECIFIED" in line, (
                    f"{metric_id} not marked SPECIFIED: {line}"
                )
                break


def test_search_metrics_m201_through_m205_specified():
    """Cycle 260: M-201 through M-205 (search metrics) must be specified."""
    spec_path = REPO / "programs" / "A_metrology" / "MeasurementEngineSpecification.md"
    spec = spec_path.read_text()
    for metric_id in ("M-201", "M-202", "M-203", "M-204", "M-205"):
        assert f"## {metric_id}:" in spec, f"Missing section header for {metric_id}"
        for line in spec.splitlines():
            if line.startswith(f"| {metric_id} "):
                assert "TODO" not in line, f"{metric_id} still marked TODO: {line}"
                assert "SPECIFIED" in line, f"{metric_id} not marked SPECIFIED: {line}"
                break


def test_evaluation_metrics_m304_through_m306_specified():
    """Cycle 260: M-304 through M-306 (evaluation metrics) must be specified."""
    spec_path = REPO / "programs" / "A_metrology" / "MeasurementEngineSpecification.md"
    spec = spec_path.read_text()
    for metric_id in ("M-304", "M-305", "M-306"):
        assert f"## {metric_id}:" in spec, f"Missing section header for {metric_id}"
        for line in spec.splitlines():
            if line.startswith(f"| {metric_id} "):
                assert "TODO" not in line, f"{metric_id} still marked TODO: {line}"
                assert "SPECIFIED" in line, f"{metric_id} not marked SPECIFIED: {line}"
                break


def test_stage_m1_acceptance_pass():
    """Stage M1 acceptance criteria must be marked PASS (30/30)."""
    spec_path = REPO / "programs" / "A_metrology" / "MeasurementEngineSpecification.md"
    spec = spec_path.read_text()
    assert "Stage M1: PASS" in spec or "**Stage M1: PASS" in spec, (
        "Stage M1 acceptance must be marked PASS"
    )
    assert "30 of 30 metrics specified (100%)" in spec


def test_no_todo_metrics_remain():
    """No metric should remain marked TODO in the inventory tables."""
    spec_path = REPO / "programs" / "A_metrology" / "MeasurementEngineSpecification.md"
    spec = spec_path.read_text()
    # Find all inventory table rows with TODO
    todo_rows = [line for line in spec.splitlines()
                 if line.startswith("| M-") and "TODO" in line]
    assert not todo_rows, (
        f"Metrics still marked TODO: {todo_rows}"
    )


def test_no_forbidden_patterns_in_source_files():
    """Scan source files for forbidden STOP BUILDING patterns.

    This is the main enforcement test. It fails CI if any forbidden
    pattern is found in a non-excluded source file.
    """
    all_violations = []
    for scan_dir in SCAN_DIRECTORIES:
        dir_path = REPO / scan_dir
        if not dir_path.exists():
            continue
        for py_file in dir_path.rglob("*.py"):
            violations = _scan_file_for_forbidden_patterns(py_file)
            for v in violations:
                all_violations.append((py_file, v))

    if all_violations:
        error_msg = ["STOP BUILDING list violations detected:"]
        for path, (line_no, pattern, message, line_content) in all_violations:
            try:
                rel = path.relative_to(REPO)
            except ValueError:
                rel = path
            error_msg.append(f"  {rel}:{line_no}: {message}")
            error_msg.append(f"    Pattern: {pattern}")
            error_msg.append(f"    Line: {line_content}")
        pytest.fail("\n".join(error_msg))


def test_gen0_proposal_composer_is_frozen():
    """The Gen0 ProposalComposer must not have been modified beyond
    the frozen state. We check that the file hasn't grown significantly
    since cycle 247 (when it was frozen).

    This is a weak check — it just verifies the file exists and is
    importable. A real freeze would use git tags.
    """
    from audit.measurement_integrity.dr92_proposal_composer import ProposalComposer, BridgeProposal
    # Smoke test: the class still exists and is importable
    composer = ProposalComposer()
    assert hasattr(composer, "compose")
    assert hasattr(composer, "_canon")


def test_programs_a_through_g_directories_exist():
    """All 7 program directories must exist (even if empty stubs)."""
    programs_dir = REPO / "programs"
    assert programs_dir.exists()
    expected_programs = [
        "A_metrology",
        "B_discovery",
        "C_proposal",
        "D_evaluation",
        "E_invention",
        "F_search",
        "G_research_infrastructure",
    ]
    for prog in expected_programs:
        assert (programs_dir / prog).exists(), f"Missing program directory: {prog}"


def test_go_no_go_gates_md_has_current_status():
    """GO_NO_GO_GATES.md must document current status of all 4 gates."""
    gates_doc = (REPO / "GO_NO_GO_GATES.md").read_text()
    assert "Gate 1 — Measurement" in gates_doc
    assert "Gate 2 — Discovery" in gates_doc
    assert "Gate 3 — Proposal" in gates_doc
    assert "Gate 4 — Invention" in gates_doc
    # Current state must be documented
    assert "NOT STARTED" in gates_doc or "BLOCKED" in gates_doc
    assert "0/4 gates PASS" in gates_doc or "0/4" in gates_doc


# ============================================================================
# Stage M2 (Measurement Provenance) — cycle 262
# ============================================================================

def test_stage_m2_provenance_infrastructure_exists():
    """Cycle 262: Stage M2 infrastructure must exist.

    Per ROADMAP_V2.md Stage M2: no naked numbers. The provenance
    infrastructure (ScoredValue, ProvenanceRegistry, @with_provenance)
    must be in place.
    """
    assert (REPO / "programs" / "A_metrology" / "measurement_provenance.py").exists()
    assert (REPO / "tests" / "test_measurement_provenance.py").exists()


def test_stage_m2_scored_value_is_importable():
    """ScoredValue must be importable from the measurement provenance module."""
    from programs.A_metrology.measurement_provenance import ScoredValue
    sv = ScoredValue(
        value=0.5, metric_id="M-test", metric_name="test",
        uncertainty_std=0.1, ci_95_lower=0.3, ci_95_upper=0.7,
        n=10, n_resamples=100, evidence_tier="B",
        calibration_version="v1", evaluator_version="v1",
        prompt_version="n/a", judge_version="n/a",
        timestamp="now", benchmark_version="v1",
    )
    assert sv.value == 0.5
    assert sv.metric_id == "M-test"


def test_stage_m2_registry_has_all_30_metrics():
    """The provenance registry must have bootstrap data for all 30 metrics."""
    from programs.A_metrology.measurement_provenance import ProvenanceRegistry
    reg = ProvenanceRegistry()
    required = (
        {f"M-{i:03d}" for i in range(1, 17)} |
        {f"M-{i:03d}" for i in range(101, 106)} |
        {f"M-{i:03d}" for i in range(201, 206)} |
        {"M-301", "M-302", "M-304", "M-305", "M-306"}
    )
    for mid in required:
        assert reg.has_metric(mid), f"Registry missing {mid}"
