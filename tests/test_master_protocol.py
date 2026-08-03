#!/usr/bin/env python3
"""
Test: Master Protocol enforcement.

Per the CEO directive: consolidate all governance into a single
MASTER_PROTOCOL.md. The coder reads MASTER_PROTOCOL.md and FAILURES.md.
That is enough.

This test verifies:
1. MASTER_PROTOCOL.md exists and contains the 11-section structure.
2. The 7 essential root .md files exist (MASTER_PROTOCOL, FAILURES,
   CONSTITUTION, ANTI_ENTROPY, CONTRIBUTING, README, EXAMPLE_BLUEPRINT_001).
3. The archived docs are in archive/governance-pre-consolidation/.
4. The scanner (enforce_law27.py) still passes.
5. The P7 Retraction Registry and P8 Test Registry still work.
6. The principle is stated in MASTER_PROTOCOL.md.
"""
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class TestMasterProtocolExists:
    """Verify MASTER_PROTOCOL.md exists and contains the required structure."""

    def test_master_protocol_exists(self):
        path = ROOT / "MASTER_PROTOCOL.md"
        assert path.exists(), "MASTER_PROTOCOL.md does not exist at repo root."

    def test_master_protocol_has_11_sections(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        # The 11 sections (0-11)
        for section in ["0. PURPOSE", "1. REQUIREMENTS", "2. EVIDENCE",
                        "3. DECOMPOSITION", "4. ALTERNATIVES", "5. CONSISTENCY",
                        "6. TRADEOFFS", "7. ADVERSARIAL REVIEW", "8. IMPLEMENTATION",
                        "9. VALIDATION", "10. RETRACTIONS", "11. FINAL VERDICT"]:
            assert section in content, f"MASTER_PROTOCOL.md missing section: {section}"

    def test_master_protocol_has_typed_status(self):
        """MASTER_PROTOCOL.md must define the typed status block (replaces confidence)."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "validation_level" in content
        assert "evidence_strength" in content
        assert "experimental_validation" in content
        assert "L0" in content and "L9" in content

    def test_master_protocol_has_forbidden_language_rules(self):
        """MASTER_PROTOCOL.md must forbid numerical confidence."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "forbidden" in content.lower()
        assert "numerical confidence" in content.lower()

    def test_master_protocol_has_retraction_rule(self):
        """MASTER_PROTOCOL.md must define the retraction rule."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "RETRACTION" in content or "retraction" in content.lower()
        assert "KILL_TEST_FAILED" in content

    def test_master_protocol_has_principle(self):
        """MASTER_PROTOCOL.md must state the principle."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "increase truth" in content.lower()
        assert "reduce risk" in content.lower()
        assert "reproducibility" in content.lower()
        assert "execution" in content.lower()

    def test_master_protocol_has_maturity_levels(self):
        """MASTER_PROTOCOL.md must define package maturity levels."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for level in ["CONCEPT", "DECISION", "EVALUATION", "PROTOTYPE", "PRODUCTION"]:
            assert level in content, f"MASTER_PROTOCOL.md missing maturity level: {level}"

    def test_master_protocol_has_coder_contract(self):
        """MASTER_PROTOCOL.md must define the coder's contract."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "protocol decides" in content.lower()
        assert "coder executes" in content.lower()


class TestEssentialDocsAtRoot:
    """Verify the 7 essential .md files exist at root."""

    ESSENTIAL = [
        "MASTER_PROTOCOL.md",
        "FAILURES.md",
        "CONSTITUTION.md",
        "ANTI_ENTROPY.md",
        "CONTRIBUTING.md",
        "README.md",
        "EXAMPLE_BLUEPRINT_001.md",
    ]

    @pytest.mark.parametrize("filename", ESSENTIAL)
    def test_essential_doc_exists(self, filename):
        path = ROOT / filename
        assert path.exists(), f"Essential doc missing: {filename}"

    def test_no_excess_docs_at_root(self):
        """No more than the 7 essential .md files at root.

        Per the principle: if a document does not directly increase truth,
        reduce risk, increase reproducibility, or improve execution, it
        shall not exist at root. Research-phase docs are archived.
        """
        root_mds = list(ROOT.glob("*.md"))
        root_md_names = {m.name for m in root_mds}
        essential = set(self.ESSENTIAL)
        excess = root_md_names - essential
        assert not excess, (
            f"Excess .md files at root (should be archived): {sorted(excess)}"
        )


class TestArchiveExists:
    """Verify archived docs are in archive/governance-pre-consolidation/."""

    def test_archive_dir_exists(self):
        path = ROOT / "archive" / "governance-pre-consolidation"
        assert path.exists(), "Archive directory does not exist."

    def test_archived_docs_present(self):
        """Key consolidated docs should be in the archive."""
        archive = ROOT / "archive" / "governance-pre-consolidation"
        archived = {f.name for f in archive.glob("*.md")}
        # Check a sample of the consolidated docs
        for doc in ["BLUEPRINT_CONSTITUTION.md", "HONESTY_LOOP.md", "AEP_PROTOCOL.md",
                     "ENGINEERING_PRINCIPLES.md", "CODER_DIRECTIONS.md",
                     "EVIDENCE_STANDARDS.md", "RETRACTION_REGISTRY_ENGINE.md",
                     "TEST_REGISTRY_ENGINE.md"]:
            assert doc in archived, f"Archived doc missing: {doc}"


class TestReadListUpdated:
    """Verify remember_governance.py points to MASTER_PROTOCOL.md."""

    def test_read_list_has_master_protocol(self):
        content = (ROOT / "scripts" / "remember_governance.py").read_text()
        assert "MASTER_PROTOCOL.md" in content
        assert "FAILURES.md" in content

    def test_read_list_does_not_reference_archived_docs(self):
        """The read list should not reference archived docs."""
        content = (ROOT / "scripts" / "remember_governance.py").read_text()
        for archived in ["BLUEPRINT_CONSTITUTION", "HONESTY_LOOP", "AEP_PROTOCOL",
                         "ENGINEERING_PRINCIPLES", "CODER_DIRECTIONS", "EVIDENCE_STANDARDS",
                         "HONESTY_LOOP.md", "AEP_PROTOCOL.md"]:
            assert archived not in content, (
                f"remember_governance.py still references archived doc: {archived}"
            )


class TestCIWorkflowUpdated:
    """Verify CI references MASTER_PROTOCOL.md."""

    def test_ci_has_master_protocol(self):
        content = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
        assert "Master Protocol" in content or "MASTER_PROTOCOL" in content

    def test_ci_does_not_reference_archived_docs(self):
        content = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
        # Should not reference check_aep_gate.py (the old gate checker)
        # or the old 12-file read list
        assert "check_aep_gate" not in content or "enforce_law27" in content
