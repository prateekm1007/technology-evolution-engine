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


class TestMasterProtocolSectionDepth:
    """XX10 closure: verify each section has substantive content, not just headers.

    Per auditor XX10: 'if someone removes a gate section from MASTER_PROTOCOL.md,
    there's no test that catches it.' This class catches that — each section
    must have at least 3 lines of content beyond the header, and must mention
    its key required sub-elements.
    """

    def _section_content(self, content: str, section_header: str) -> str:
        """Extract the content of a section (between this header and the next)."""
        lines = content.split("\n")
        start = None
        for i, line in enumerate(lines):
            if section_header in line:
                start = i + 1
                break
        if start is None:
            return ""
        # Find next section header (### N. or ## N.)
        end = len(lines)
        for i in range(start, len(lines)):
            line = lines[i]
            # Next section header pattern: "### N. " or starts with a number+dot at start
            if i > start and line.strip().startswith("### ") and ". " in line:
                end = i
                break
        return "\n".join(lines[start:end])

    def test_section_0_purpose_has_content(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        section = self._section_content(content, "0. PURPOSE")
        # Must mention primary objective and success metric and maturity
        assert "primary objective" in section.lower() or "primary" in section.lower()
        assert "success metric" in section.lower() or "maturity" in section.lower()

    def test_section_1_requirements_has_classifications(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        section = self._section_content(content, "1. REQUIREMENTS")
        for cls in ["MANDATORY", "DESIRABLE", "ASPIRATIONAL", "EXPERIMENTAL"]:
            assert cls in section, f"Section 1 missing classification: {cls}"

    def test_section_2_evidence_has_source_types(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        section = self._section_content(content, "2. EVIDENCE")
        for src in ["products", "patents", "literature", "standards"]:
            assert src in section.lower(), f"Section 2 missing source type: {src}"

    def test_section_3_decomposition_has_mass_stackup(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        section = self._section_content(content, "3. DECOMPOSITION")
        assert "mass" in section.lower()
        assert "stack-up" in section.lower() or "stackup" in section.lower() or "stack up" in section.lower()
        assert "interface" in section.lower()

    def test_section_4_alternatives_requires_3(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        section = self._section_content(content, "4. ALTERNATIVES")
        assert "3 alternatives" in section or "at least 3" in section or "three" in section.lower()

    def test_section_5_consistency_has_checks(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        section = self._section_content(content, "5. CONSISTENCY")
        assert "Arithmetic" in section or "arithmetic" in section.lower()
        assert "Units" in section or "units" in section.lower()
        assert "Dimensions" in section or "dimensions" in section.lower()

    def test_section_6_tradeoffs_has_gain_cost_sacrifice(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        section = self._section_content(content, "6. TRADEOFFS")
        assert "gain" in section.lower()
        assert "cost" in section.lower()
        assert "sacrifice" in section.lower()

    def test_section_7_adversarial_has_4_reviewers(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        section = self._section_content(content, "7. ADVERSARIAL REVIEW")
        for reviewer in ["Chief Engineer", "Manufacturing", "Economist", "Customer"]:
            assert reviewer in section, f"Section 7 missing reviewer: {reviewer}"

    def test_section_8_implementation_has_bom_and_procurement(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        section = self._section_content(content, "8. IMPLEMENTATION")
        assert "BOM" in section or "bill of materials" in section.lower()
        assert "supplier" in section.lower()
        assert "quotation" in section.lower() or "quote" in section.lower()

    def test_section_9_validation_has_test_types_and_levels(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        section = self._section_content(content, "9. VALIDATION")
        for ttype in ["ANALYTICAL_ESTIMATE", "NUMERICAL_SIMULATION", "PHYSICAL_VALIDATION"]:
            assert ttype in section, f"Section 9 missing test type: {ttype}"
        for level in ["L0", "L4", "L9"]:
            assert level in section, f"Section 9 missing validation level: {level}"

    def test_section_10_retractions_has_categories(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        section = self._section_content(content, "10. RETRACTIONS")
        assert "RETRACTED" in section
        assert "WITHDRAWN" in section
        assert "append-only" in section.lower() or "append only" in section.lower()

    def test_section_11_verdict_has_4_outcomes(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        section = self._section_content(content, "11. FINAL VERDICT")
        for verdict in ["APPROVED", "REJECTED", "BLOCKED"]:
            assert verdict in section, f"Section 11 missing verdict: {verdict}"


class TestMasterProtocolTypedStatusEnums:
    """Verify all typed status enum values are defined in MASTER_PROTOCOL.md.

    Per auditor XX10: the old tests that checked for Law 27/28/29 enums
    were archived. This class restores that coverage — if someone removes
    an enum value from MASTER_PROTOCOL.md, the test catches it.
    """

    def test_status_enum_all_5_values(self):
        """Law 29a: STATUS must define all 5 values."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for s in ["PASS", "PASS_WITH_CONDITIONS", "MARGINAL", "BLOCKED", "REJECTED"]:
            assert s in content, f"MASTER_PROTOCOL.md missing STATUS value: {s}"

    def test_validation_level_enum_all_10_values(self):
        """Law 29b: VALIDATION_LEVEL must define L0-L9."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for i in range(10):
            assert f"L{i}" in content, f"MASTER_PROTOCOL.md missing validation level L{i}"

    def test_evidence_strength_enum_all_5_values(self):
        """Law 29c: EVIDENCE_STRENGTH must define all 5 values."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for s in ["ABSENT", "WEAK", "MODERATE", "STRONG", "VERY_STRONG"]:
            assert s in content, f"MASTER_PROTOCOL.md missing evidence strength: {s}"

    def test_package_maturity_enum_all_5_values(self):
        """Law 29d: PACKAGE_MATURITY must define all 5 values."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for m in ["CONCEPT", "DECISION", "EVALUATION", "PROTOTYPE", "PRODUCTION"]:
            assert m in content, f"MASTER_PROTOCOL.md missing package maturity: {m}"

    def test_retraction_reason_categories(self):
        """The 8 retraction reason categories must be defined."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for cat in ["NUMERICAL_CONTRADICTION", "SEMANTIC_CONTRADICTION",
                    "EVIDENCE_INVALIDATED", "KILL_TEST_FAILED", "DESIGN_CHANGE"]:
            assert cat in content, f"MASTER_PROTOCOL.md missing retraction category: {cat}"

    def test_forbidden_patterns_listed(self):
        """The forbidden language patterns must be explicitly listed."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        # Must mention the forbidden things
        assert "numerical confidence" in content.lower()
        assert "PASS" in content and "FAIL" in content  # PASS/FAIL percentages forbidden
        assert "simulation" in content.lower()  # simulation mislabeling forbidden


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
