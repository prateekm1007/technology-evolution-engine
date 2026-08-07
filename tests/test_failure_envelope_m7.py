"""
test_failure_envelope_m7.py — Tests for Stage M7 (Failure Envelope).

Verifies:
  1. FailureEnvelope dataclass has all required fields
  2. to_markdown produces complete documents
  3. reports/failure_envelopes/ directory exists with 38 .md files
  4. Every envelope has known failure modes, boundary conditions, repair recommendations
  5. Summary reports (JSON + MD) exist with correct structure
  6. Specific metrics have expected failure modes (M-008 FP floor, M-010 fragile, etc.)
"""
import sys
import json
from pathlib import Path
from dataclasses import fields as dataclass_fields

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from programs.A_metrology.failure_envelope_m7 import (
    FailureEnvelope, generate_all_envelopes, FAILURE_MODE_KB,
)


# ============================================================================
# FailureEnvelope dataclass
# ============================================================================

def test_failure_envelope_has_all_required_fields():
    """FailureEnvelope must have all required fields."""
    field_names = {f.name for f in dataclass_fields(FailureEnvelope)}
    required = {
        "metric_id", "metric_name", "baseline_value", "ci_95", "n",
        "is_degenerate", "repeatability_verdict", "cv",
        "fragile_perturbations", "known_failure_modes",
        "boundary_conditions", "failure_signatures",
        "repair_recommendations", "evidence_refs",
    }
    missing = required - field_names
    assert not missing, f"FailureEnvelope missing fields: {missing}"


def test_failure_envelope_to_dict():
    env = FailureEnvelope(
        metric_id="M-001", metric_name="test", baseline_value=0.0,
        ci_95=(0.0, 0.0), n=20, is_degenerate=True,
        repeatability_verdict="DETERMINISTIC", cv=0.0,
        fragile_perturbations=[], known_failure_modes=["test mode"],
        boundary_conditions=["test condition"], failure_signatures=["test signature"],
        repair_recommendations=["test repair"], evidence_refs=["test ref"],
    )
    d = env.to_dict()
    assert d["metric_id"] == "M-001"
    assert d["is_degenerate"] is True
    assert d["ci_95"] == [0.0, 0.0]


def test_failure_envelope_to_markdown_has_all_sections():
    env = FailureEnvelope(
        metric_id="M-001", metric_name="test", baseline_value=0.5,
        ci_95=(0.3, 0.7), n=20, is_degenerate=False,
        repeatability_verdict="STABLE", cv=0.02,
        fragile_perturbations=[], known_failure_modes=["mode 1"],
        boundary_conditions=["condition 1"], failure_signatures=["sig 1"],
        repair_recommendations=["repair 1"], evidence_refs=["ref 1"],
    )
    md = env.to_markdown()
    assert "# Failure Envelope: M-001" in md
    assert "## Normal operating range" in md
    assert "## Known failure modes" in md
    assert "## Boundary conditions" in md
    assert "## Failure signatures" in md
    assert "## Repair recommendations" in md
    assert "## Evidence references" in md


# ============================================================================
# FAILURE_MODE_KB knowledge base
# ============================================================================

def test_failure_mode_kb_has_all_30_specified_metrics():
    """The KB must have entries for all 30 specified metrics (plus M-303 variants)."""
    required = (
        {f"M-{i:03d}" for i in range(1, 17)} |
        {f"M-{i:03d}" for i in range(101, 106)} |
        {f"M-{i:03d}" for i in range(201, 206)} |
        {"M-301", "M-302", "M-304", "M-305", "M-306"}
    )
    for mid in required:
        assert mid in FAILURE_MODE_KB, f"KB missing {mid}"


def test_failure_mode_kb_m008_has_fp_floor_finding():
    """M-008 KB entry must document the FP floor = 1.0 catastrophic finding."""
    kb = FAILURE_MODE_KB["M-008"]
    all_text = " ".join(kb["known_failure_modes"])
    assert "CATASTROPHIC" in all_text or "catastrophic" in all_text.lower()


def test_failure_mode_kb_m010_has_fragility_finding():
    """M-010 KB entry must document the M6 fragility finding."""
    kb = FAILURE_MODE_KB["M-010"]
    all_text = " ".join(kb["known_failure_modes"])
    assert "FRAGILE" in all_text or "fragile" in all_text.lower()


def test_failure_mode_kb_m105_has_dr91_invalidation():
    """M-105 KB entry must document the DR-91 invalidation."""
    kb = FAILURE_MODE_KB["M-105"]
    all_text = " ".join(kb["known_failure_modes"])
    assert "DR-91" in all_text or "invalidated" in all_text.lower()


# ============================================================================
# End-to-end: reports exist
# ============================================================================

def test_failure_envelopes_directory_exists():
    """reports/failure_envelopes/ must exist with .md files."""
    dirpath = REPO / "reports" / "failure_envelopes"
    assert dirpath.exists()
    assert dirpath.is_dir()


def test_failure_envelope_files_count():
    """At least 30 failure envelope .md files must exist (one per specified metric)."""
    dirpath = REPO / "reports" / "failure_envelopes"
    md_files = list(dirpath.glob("*.md"))
    assert len(md_files) >= 30, (
        f"Expected >= 30 failure envelope files, got {len(md_files)}"
    )


def test_failure_envelope_m008_file_exists():
    """M-008 (FP floor) must have a failure envelope file."""
    assert (REPO / "reports" / "failure_envelopes" / "M-008.md").exists()


def test_failure_envelope_m010_file_exists():
    """M-010 (per-proposal F1) must have a failure envelope file."""
    assert (REPO / "reports" / "failure_envelopes" / "M-010.md").exists()


def test_failure_envelope_m105_file_exists():
    """M-105 (Gen 5 Discovery F1) must have a failure envelope file."""
    assert (REPO / "reports" / "failure_envelopes" / "M-105.md").exists()


def test_failure_envelope_json_exists():
    """reports/failure_envelope_m7.json must exist."""
    assert (REPO / "reports" / "failure_envelope_m7.json").exists()


def test_failure_envelope_md_exists():
    """reports/failure_envelope_m7.md must exist."""
    assert (REPO / "reports" / "failure_envelope_m7.md").exists()


# ============================================================================
# JSON structure
# ============================================================================

def test_json_has_required_structure():
    """JSON must have cycle, stage, n_envelopes, gate_verdict, envelopes."""
    path = REPO / "reports" / "failure_envelope_m7.json"
    data = json.loads(path.read_text())
    assert data["stage"] == "M7"
    assert data["program"] == "A"
    assert "n_envelopes" in data
    assert "gate_verdict" in data
    assert "envelopes" in data
    assert isinstance(data["envelopes"], list)
    assert len(data["envelopes"]) >= 30


def test_every_envelope_has_required_fields():
    """Each envelope in JSON must have all required fields."""
    path = REPO / "reports" / "failure_envelope_m7.json"
    data = json.loads(path.read_text())
    required = {
        "metric_id", "baseline_value", "is_degenerate",
        "known_failure_modes", "boundary_conditions",
        "repair_recommendations",
    }
    for e in data["envelopes"]:
        assert required.issubset(e.keys()), (
            f"Envelope {e.get('metric_id', '?')} missing: {required - set(e.keys())}"
        )


def test_all_envelopes_have_failure_modes():
    """Every envelope must have at least 1 known failure mode."""
    path = REPO / "reports" / "failure_envelope_m7.json"
    data = json.loads(path.read_text())
    for e in data["envelopes"]:
        assert len(e["known_failure_modes"]) >= 1, (
            f"{e['metric_id']} has 0 known failure modes"
        )


def test_all_envelopes_have_boundary_conditions():
    """Every envelope must have at least 1 boundary condition."""
    path = REPO / "reports" / "failure_envelope_m7.json"
    data = json.loads(path.read_text())
    for e in data["envelopes"]:
        assert len(e["boundary_conditions"]) >= 1, (
            f"{e['metric_id']} has 0 boundary conditions"
        )


def test_all_envelopes_have_repair_recommendations():
    """Every envelope must have at least 1 repair recommendation."""
    path = REPO / "reports" / "failure_envelope_m7.json"
    data = json.loads(path.read_text())
    for e in data["envelopes"]:
        assert len(e["repair_recommendations"]) >= 1, (
            f"{e['metric_id']} has 0 repair recommendations"
        )


# ============================================================================
# Specific metric checks
# ============================================================================

def test_m008_envelope_documents_fp_floor():
    """M-008 envelope must document the FP floor = 1.0 catastrophic finding."""
    path = REPO / "reports" / "failure_envelope_m7.json"
    data = json.loads(path.read_text())
    m008 = next(e for e in data["envelopes"] if e["metric_id"] == "M-008")
    all_text = " ".join(m008["known_failure_modes"])
    assert "CATASTROPHIC" in all_text or "1.0" in all_text


def test_m010_envelope_documents_repair():
    """M-010 envelope should document the repair (cycle 269).
    Previously had 2 FRAGILE perturbations; now 0 after repair
    (using ALL shared entities instead of just the first)."""
    path = REPO / "reports" / "failure_envelope_m7.json"
    data = json.loads(path.read_text())
    m010 = next(e for e in data["envelopes"] if e["metric_id"] == "M-010")
    # After repair (cycle 269), M-010 should have 0 FRAGILE perturbations
    assert len(m010["fragile_perturbations"]) == 0, (
        f"M-010 should have 0 FRAGILE after repair, got {len(m010['fragile_perturbations'])}"
    )


def test_m105_envelope_documents_dr91_invalidation():
    """M-105 envelope must document the DR-91 invalidation."""
    path = REPO / "reports" / "failure_envelope_m7.json"
    data = json.loads(path.read_text())
    m105 = next(e for e in data["envelopes"] if e["metric_id"] == "M-105")
    all_text = " ".join(m105["known_failure_modes"])
    assert "DR-91" in all_text or "invalidated" in all_text.lower()


def test_m305_envelope_documents_bias():
    """M-305 envelope must document the +2.50 self-validation bias."""
    path = REPO / "reports" / "failure_envelope_m7.json"
    data = json.loads(path.read_text())
    m305 = next(e for e in data["envelopes"] if e["metric_id"] == "M-305")
    all_text = " ".join(m305["known_failure_modes"])
    assert "2.50" in all_text or "bias" in all_text.lower()


def test_gate_verdict_is_pass():
    """Gate M7 verdict should be PASS (all envelopes complete)."""
    path = REPO / "reports" / "failure_envelope_m7.json"
    data = json.loads(path.read_text())
    assert data["gate_verdict"] == "PASS"


# ============================================================================
# Markdown file content checks
# ============================================================================

def test_m008_md_file_has_all_sections():
    """M-008 .md file must have all required sections."""
    path = REPO / "reports" / "failure_envelopes" / "M-008.md"
    content = path.read_text()
    assert "# Failure Envelope: M-008" in content
    assert "## Normal operating range" in content
    assert "## Known failure modes" in content
    assert "## Boundary conditions" in content
    assert "## Failure signatures" in content
    assert "## Repair recommendations" in content
    assert "## Evidence references" in content


def test_m010_md_file_documents_fragile_perturbations():
    """M-010 .md file must have a Fragile perturbations table."""
    path = REPO / "reports" / "failure_envelopes" / "M-010.md"
    content = path.read_text()
    assert "## Fragile perturbations" in content or "FRAGILE" in content
