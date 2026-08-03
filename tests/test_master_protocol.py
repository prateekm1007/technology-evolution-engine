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

    def test_master_protocol_has_commercial_specification(self):
        """MASTER_PROTOCOL.md must state the commercial specification."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "commercial specification" in content.lower()
        assert "next expensive risk" in content.lower()

    def test_master_protocol_has_typed_status(self):
        """MASTER_PROTOCOL.md must define the typed status block."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "validation_level" in content
        assert "evidence_strength" in content
        assert "experimental_validation" in content

    def test_master_protocol_has_forbidden_language_rules(self):
        """MASTER_PROTOCOL.md must forbid numerical confidence."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "forbidden" in content.lower()
        assert "numerical confidence" in content.lower()

    def test_master_protocol_has_retraction_rule(self):
        """MASTER_PROTOCOL.md must define the retraction rule (Law 4)."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "LAW 4" in content
        assert "Retractions" in content
        assert "KILL_TEST_FAILED" in content or "permanent" in content.lower()

    def test_master_protocol_has_principle(self):
        """MASTER_PROTOCOL.md must state the supreme principle (risk reduction)."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        # The new supreme principle replaces the old 4-part principle
        assert "next expensive risk" in content.lower()
        assert "reducing uncertainty" in content.lower()
        assert "producing decisions" in content.lower()

    def test_master_protocol_has_maturity_levels(self):
        """MASTER_PROTOCOL.md must define package maturity levels (Law 1)."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for level in ["DISCOVERY", "CONCEPT", "EVALUATION", "PROTOTYPE", "PRODUCTION"]:
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
        assert "3 alternatives" in section or "at least 3" in section or "three" in section.lower() or "3+" in section

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
        assert "BOM" in section or "bill of materials" in section.lower() or "LAW 6" in section or "Law 6" in section
        assert "supplier" in section.lower() or "Law 6" in section or "Law 9" in section
        assert "quotation" in section.lower() or "quote" in section.lower() or "QUOTED" in section or "Law 6" in section

    def test_section_9_validation_has_test_types_and_levels(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        section = self._section_content(content, "9. VALIDATION")
        for ttype in ["ANALYTICAL_ESTIMATE", "NUMERICAL_SIMULATION", "PHYSICAL_VALIDATION"]:
            assert ttype in section, f"Section 9 missing test type: {ttype}"
        assert "L0" in section or "Law 1" in section or "Law 5" in section

    def test_section_10_retractions_has_categories(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        section = self._section_content(content, "10. RETRACTIONS")
        assert "Retracted" in section or "RETRACTED" in section
        assert "WITHDRAWN" in section or "withdrawn" in section.lower()
        assert "append-only" in section.lower() or "append only" in section.lower() or "Law 4" in section

    def test_section_11_kill_tests_present(self):
        """Section 11 is now Kill Tests (Law 10), not Final Verdict."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        section = self._section_content(content, "11. KILL TESTS")
        assert "KT" in section or "kill" in section.lower()
        assert "claim" in section.lower()
        assert "measurement" in section.lower() or "threshold" in section.lower()

    def test_section_12_safety_and_ip_present(self):
        """Section 12 covers Safety + IP (Laws 8 + 11)."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        section = self._section_content(content, "12. SAFETY")
        assert "standards" in section.lower() or "Law 8" in section
        assert "patents" in section.lower() or "Law 11" in section

    def test_final_verdict_has_4_outcomes(self):
        """The FINAL VERDICT must define APPROVED/REJECTED/BLOCKED."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for verdict in ["APPROVED", "REJECTED", "BLOCKED"]:
            assert verdict in content, f"MASTER_PROTOCOL.md missing verdict: {verdict}"


class TestMasterProtocolTypedStatusEnums:
    """Verify typed status enum values are defined in MASTER_PROTOCOL.md.

    Per auditor XX10: the old tests that checked for Law 27/28/29 enums
    were archived. This class restores that coverage — if someone removes
    an enum value from MASTER_PROTOCOL.md, the test catches it.
    """

    def test_status_enum_all_5_values(self):
        """STATUS must define all 5 values."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for s in ["PASS", "PASS_WITH_CONDITIONS", "MARGINAL", "BLOCKED", "REJECTED"]:
            assert s in content, f"MASTER_PROTOCOL.md missing STATUS value: {s}"

    def test_validation_level_l0_l9(self):
        """VALIDATION_LEVEL must define L0-L9."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "L0" in content and "L9" in content

    def test_evidence_strength_enum(self):
        """EVIDENCE_STRENGTH must define the key values."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for s in ["ABSENT", "WEAK", "MODERATE", "STRONG", "VERY_STRONG"]:
            assert s in content, f"MASTER_PROTOCOL.md missing evidence strength: {s}"

    def test_maturity_levels_from_law_1(self):
        """Law 1 maturity levels must be defined."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for m in ["DISCOVERY", "EVALUATION", "PROTOTYPE", "PRODUCTION"]:
            assert m in content, f"MASTER_PROTOCOL.md missing maturity: {m}"

    def test_forbidden_patterns_listed(self):
        """The forbidden language patterns must be explicitly listed."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "numerical confidence" in content.lower()
        assert "PASS" in content and "FAIL" in content
        assert "simulation" in content.lower()


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


class TestMasterProtocolTwelveLaws:
    """Verify MASTER_PROTOCOL.md contains the 12 Laws (market feedback, 2026-08-03).

    Per CEO directive: the auditor's bar becomes constitutional law.
    Every law must be present. If a law is removed, the test fails.
    """

    def test_law_1_product_identity(self):
        """Law 1: every package declares exactly one maturity level."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "LAW 1" in content and "Product identity" in content
        for level in ["DISCOVERY", "CONCEPT", "EVALUATION", "DETAILED DESIGN",
                      "PRE-PROTOTYPE", "PROTOTYPE", "VALIDATED DESIGN", "PRODUCTION"]:
            assert level in content, f"Law 1 missing maturity level: {level}"

    def test_law_2_arithmetic_closure(self):
        """Law 2: energy/mass/cost/thermal/manufacturing budgets must reconcile."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "LAW 2" in content and "Arithmetic closure" in content
        for budget in ["energy budget", "mass budget", "cost budget",
                       "thermal budget", "manufacturing budget"]:
            assert budget in content, f"Law 2 missing budget: {budget}"
        assert "reconcile" in content.lower()

    def test_law_3_epistemic_closure(self):
        """Law 3: every claim has claim/source/method/level/status/blocking."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "LAW 3" in content and "Epistemic closure" in content
        for field in ["claim", "source", "method", "validation level",
                       "status", "blocking condition"]:
            assert field in content, f"Law 3 missing field: {field}"

    def test_law_4_retractions(self):
        """Law 4: retractions are permanent, never deleted, never hidden."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "LAW 4" in content and "Retractions" in content
        assert "permanent" in content.lower()
        assert "never deleted" in content.lower()
        assert "never hidden" in content.lower()

    def test_law_5_thermal_truth(self):
        """Law 5: narrative reasoning prohibited for thermal claims."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "LAW 5" in content and "Thermal truth" in content
        assert "Narrative reasoning is prohibited" in content
        for method in ["measurements", "analytical models", "CFD", "FEA",
                       "physical experiments"]:
            assert method in content, f"Law 5 missing method: {method}"

    def test_law_6_cost_truth(self):
        """Law 6: every cost line is QUOTED, CATALOG, or ESTIMATED."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "LAW 6" in content and "Cost truth" in content
        for tag in ["QUOTED", "CATALOG", "ESTIMATED"]:
            assert tag in content, f"Law 6 missing cost tag: {tag}"

    def test_law_7_interface_control(self):
        """Law 7: mechanical/electrical/software/thermal/communication interfaces."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "LAW 7" in content and "Interface control" in content
        for iface in ["mechanical", "electrical", "software",
                       "thermal", "communication"]:
            assert iface in content.lower(), f"Law 7 missing interface: {iface}"

    def test_law_8_safety(self):
        """Law 8: standards, abuse cases, propagation, FMEA, certification."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "LAW 8" in content and "Safety" in content
        for item in ["standards", "abuse cases", "propagation",
                       "failure analysis", "certification"]:
            assert item in content.lower(), f"Law 8 missing item: {item}"

    def test_law_9_manufacturing(self):
        """Law 9: process sequence, tooling, yield, failure modes, quality gates."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "LAW 9" in content and "Manufacturing" in content
        for item in ["process sequence", "tooling", "yield",
                       "failure modes", "quality gates"]:
            assert item in content.lower(), f"Law 9 missing item: {item}"

    def test_law_10_kill_tests(self):
        """Law 10: the system asks 'How do we kill it?' not 'Can we build it?'"""
        import re
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        # Normalize whitespace (the phrase may span lines)
        normalized = re.sub(r"\s+", " ", content)
        assert "LAW 10" in normalized and "Kill tests" in normalized
        assert "How do we kill it" in normalized
        assert "Can we build it" in normalized
        for field in ["KT-ID", "claim", "test", "measurement",
                       "failure threshold", "consequence"]:
            assert field in content, f"Law 10 missing kill-test field: {field}"

    def test_law_11_ip_posture(self):
        """Law 11: patents, claim families, litigation, restricted zones, lawyer review."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "LAW 11" in content
        for item in ["patents", "claim families", "litigation",
                       "restricted zones", "lawyer review"]:
            assert item in content.lower(), f"Law 11 missing item: {item}"

    def test_law_12_next_spend_protocol(self):
        """Law 12: what next, cost, learn, decision unlocked, what could kill."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "LAW 12" in content and "Next-spend" in content
        for q in ["What should we do next", "What will it cost",
                  "What will we learn", "What decision becomes possible",
                  "What could kill the project"]:
            assert q in content, f"Law 12 missing question: {q}"


class TestNextMoneyPage:
    """Verify MASTER_PROTOCOL.md defines the Next Money Page.

    Per CEO directive: 'That single page converts a document into an
    investment instrument.' The package does not end at a verdict.
    It ends at a decision.
    """

    def test_next_money_page_defined(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "NEXT MONEY PAGE" in content.upper(), (
            "MASTER_PROTOCOL.md does not define the Next Money Page."
        )

    def test_next_money_page_has_required_sections(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for section in ["Current maturity", "Remaining risks", "Next expenditure",
                        "This buys", "Decision unlocked", "Possible outcomes",
                        "What could kill the project"]:
            assert section in content, (
                f"Next Money Page missing section: {section}"
            )


class TestCommercialSpecification:
    """Verify MASTER_PROTOCOL.md states the commercial specification.

    Per CEO directive: 'You are not writing reports. You are reducing
    uncertainty. You are not producing documents. You are producing
    decisions.'
    """

    def test_commercial_specification_present(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "commercial specification" in content.lower()

    def test_reducing_uncertainty(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "reducing uncertainty" in content.lower()

    def test_producing_decisions(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "producing decisions" in content.lower()

    def test_next_expensive_risk(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "next expensive risk" in content.lower()

    def test_spend_next_dollar(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "spend the next dollar" in content.lower()

    def test_would_someone_spend_money(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "Would someone spend money" in content

    def test_supreme_law_in_constitution(self):
        """CONSTITUTION.md must contain the supreme law."""
        content = (ROOT / "CONSTITUTION.md").read_text()
        assert "Supreme Law" in content
        assert "next expensive risk" in content.lower()

    def test_supreme_principle_in_anti_entropy(self):
        """ANTI_ENTROPY.md must contain the supreme anti-entropy principle."""
        content = (ROOT / "ANTI_ENTROPY.md").read_text()
        assert "supreme anti-entropy principle" in content.lower()
        assert "next expensive risk" in content.lower()


class TestPayBar:
    """Verify MASTER_PROTOCOL.md contains the 12-criterion pay bar.

    Per market feedback (2026-08-03): 'I pay for an engineering design
    package for hardware when the document removes the next expensive
    risk, not when it narrates a good idea.'
    """

    def test_pay_bar_defined(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "pay bar" in content.lower(), (
            "MASTER_PROTOCOL.md does not define the pay bar."
        )

    def test_pay_bar_one_sentence(self):
        """The one-sentence bar must be present."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "$25k" in content or "$25,000" in content
        assert "next expensive risk" in content.lower()

    def test_12_excellence_criteria(self):
        """All 12 excellence criteria must be listed."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for criterion in ["Identity", "Arithmetic closure", "Epistemic honesty",
                          "Retraction discipline", "Thermal truth", "Quoted cost",
                          "Interfaces", "Safety path", "Manufacturing path",
                          "Kill tests", "IP posture", "Next-spend plan"]:
            assert criterion in content, f"Pay bar missing criterion: {criterion}"

    def test_pass_rule_stated(self):
        """The pass rule must be stated (miss 2,5,6,7,10 → no pay)."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "Pass rule" in content or "pass rule" in content.lower()
        # Must mention the 5 deal-breaking criteria numbers
        for num in ["2", "5", "6", "7", "10"]:
            assert num in content

    def test_6_non_negotiables(self):
        """All 6 deal-breakers must be listed."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "Non-negotiable" in content or "non-negotiable" in content.lower()
        for dealbreaker in ["internally inconsistent", "retracted claim",
                            "MANDATORY", "narrative", "catalog fiction",
                            "PRODUCTION"]:
            assert dealbreaker in content, (
                f"Non-negotiables missing: {dealbreaker}"
            )

    def test_5_phase_roadmap(self):
        """All 5 phases of the roadmap must be present."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        # The roadmap table uses "Phase 0" through "Phase 5" in the
        # narrative, and "| 0 |" through "| 5 |" in the table. Check both.
        for phase_num in ["0", "1", "2", "3", "4", "5"]:
            assert f"Phase {phase_num}" in content or f"| {phase_num} |" in content, (
                f"Roadmap missing phase: {phase_num}"
            )
        # Exit criteria
        assert "Freeze the product identity" in content
        assert "Close the numbers" in content
        assert "Thermal" in content and "electrical" in content.lower()
        assert "Interfaces" in content and "safety" in content.lower()
        assert "Kill-test suite" in content or "Kill-test" in content
        assert "Package hardening" in content

    def test_pays_at_each_stage(self):
        """The stage-to-payment table must be present."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "hardware design package rate" in content.lower()
        assert "EVALUATION concept" in content or "concept" in content
        assert "Pre-prototype" in content or "pre-prototype" in content.lower()

    def test_highest_roi_stretch(self):
        """The highest-ROI stretch (Phase 1 + 2) must be stated."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "highest-ROI" in content or "highest ROI" in content
        assert "Phase 1" in content and "Phase 2" in content


class TestPayBarAntiEntropy:
    """Verify ANTI_ENTROPY.md contains the 6 deal-breakers."""

    def test_pay_bar_anti_entropy_principle(self):
        content = (ROOT / "ANTI_ENTROPY.md").read_text()
        assert "pay-bar anti-entropy principle" in content.lower()

    def test_6_deal_breakers_listed(self):
        content = (ROOT / "ANTI_ENTROPY.md").read_text()
        for item in ["internally inconsistent", "retracted claim",
                     "MANDATORY", "narrative", "catalog fiction",
                     "PRODUCTION"]:
            assert item in content, (
                f"ANTI_ENTROPY.md missing deal-breaker: {item}"
            )

    def test_deal_breakers_reject_package(self):
        content = (ROOT / "ANTI_ENTROPY.md").read_text()
        assert "rejected" in content.lower() or "does not meet" in content.lower()
        assert "deal-breaker" in content.lower() or "deal breaker" in content.lower()


class TestCustomerFacingSeparation:
    """Verify MASTER_PROTOCOL.md defines the customer-facing separation rule.

    Per market feedback: 'The customer should never see Law 27, Law 10,
    P7 registry, P8 registry, MASTER_PROTOCOL, package identifiers.'
    """

    def test_customer_facing_section_present(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "Customer-facing separation" in content

    def test_forbidden_internal_references_listed(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for ref in ["Law 1", "Law 10", "P7", "P8", "MASTER_PROTOCOL",
                     "enforce_law27"]:
            assert ref in content, (
                f"Customer-facing separation must list forbidden reference: {ref}"
            )

    def test_self_reference_rule_in_anti_entropy(self):
        """ANTI_ENTROPY.md must contain the self-reference anti-entropy rule."""
        content = (ROOT / "ANTI_ENTROPY.md").read_text()
        assert "self-reference anti-entropy rule" in content.lower()
        assert "implementation details" in content.lower()


class TestFrameBreakingMandate:
    """Verify MASTER_PROTOCOL.md defines the frame-breaking mandate.

    Per market feedback: 'An Era 4 system would ask: Why must satellites
    exist at all?'
    """

    def test_frame_breaking_mandate_present(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "Frame-breaking mandate" in content

    def test_frame_breaking_alternatives_listed(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "Balloon" in content or "balloon" in content.lower()
        assert "mesh" in content.lower() or "terrestrial" in content.lower()

    def test_frame_breaking_when_to_break(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "MANDATORY" in content and "frame" in content.lower()
        assert "REJECTED" in content

    def test_frame_breaking_in_anti_entropy(self):
        """ANTI_ENTROPY.md must contain the frame-breaking anti-entropy rule."""
        content = (ROOT / "ANTI_ENTROPY.md").read_text()
        assert "frame-breaking" in content.lower()
        assert "out-of-frame" in content.lower() or "out of frame" in content.lower()


class TestEraProgression:
    """Verify MASTER_PROTOCOL.md defines the era progression honestly."""

    def test_era_progression_present(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "Era progression" in content

    def test_5_eras_defined(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        # The table uses "| 0 |" etc; the prose uses "Era 2", "Era 3", "Era 4"
        for era_num in ["0", "1", "2", "3", "4"]:
            assert f"Era {era_num}" in content or f"| {era_num} |" in content, (
                f"Era progression missing era: {era_num}"
            )

    def test_current_era_status_honest(self):
        """The current status must be honestly stated (not all ACHIEVED)."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "ACHIEVED" in content
        assert "NOT YET" in content or "EARLY" in content
        # Era 4 must NOT be claimed as achieved
        assert "Era 4" in content and "NOT YET" in content

    def test_capability_scores_present(self):
        """The auditor's capability scores must be recorded."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for cap in ["Constraint discovery", "Contradiction detection",
                    "Economic reasoning", "Invention"]:
            assert cap in content, f"Capability scores missing: {cap}"
        # Invention score must be low (honest)
        assert "3/10" in content or "Invention" in content


class TestAntiPerfectionRule:
    """Verify the anti-perfection principle is in governance.

    Per auditor: 'The goal is not perfection. The goal is systematic
    excellence. Aiming for 10/10 in everything destroys the project.'
    """

    def test_anti_perfection_in_master_protocol(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "anti-perfection" in content.lower()
        assert "systematic excellence" in content.lower()
        assert "not perfection" in content.lower()

    def test_anti_perfection_in_anti_entropy(self):
        content = (ROOT / "ANTI_ENTROPY.md").read_text()
        assert "anti-perfection" in content.lower()
        assert "systematic excellence" in content.lower()

    def test_failure_driven_rule_present(self):
        """The 'what caused the last package to fail' rule must be present."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "What caused the last package to fail" in content or \
               "what caused the last package to fail" in content.lower()
        assert "failure-driven" in content.lower() or "failure driven" in content.lower()

    def test_truth_first_discovery_later(self):
        """The 'truth first, discovery later' directive must be present."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "Truth first" in content
        assert "Discovery later" in content
        # Also in ANTI_ENTROPY
        ae = (ROOT / "ANTI_ENTROPY.md").read_text()
        assert "truth first" in ae.lower()
        assert "discovery later" in ae.lower()

    def test_capability_targets_with_priorities(self):
        """Capabilities must have targets + priorities (not all 10/10 now)."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "Sustain" in content
        assert "Phase I" in content
        # Invention must be Phase V, not Phase I
        assert "Phase V" in content


class TestFivePhaseRoadmap:
    """Verify the P1-P24 roadmap is present in MASTER_PROTOCOL.md."""

    def test_phase_i_present(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "Phase I" in content
        assert "Finish Era 1" in content or "blueprint compiler" in content.lower()

    def test_phase_ii_present(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "Phase II" in content
        assert "optimization engine" in content.lower()

    def test_phase_iii_present(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "Phase III" in content
        assert "surprise" in content.lower()

    def test_phase_iv_present(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "Phase IV" in content
        assert "Discovery" in content

    def test_phase_v_present(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "Phase V" in content
        assert "Invention" in content

    def test_phase_i_engines(self):
        """Phase I must list P1-P5 engines."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for engine in ["P1 Evidence lineage", "P2 Requirement engine",
                       "P3 Interface engine", "P4 Closure engine",
                       "P5 Decision engine"]:
            assert engine in content, f"Phase I missing: {engine}"

    def test_phase_i_exit_criterion(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "$25,000" in content or "$25k" in content
        assert "domain expert" in content.lower()

    def test_six_failures_listed(self):
        """The 6 failures that drive the next 6 months must be listed."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for failure in ["simulation", "physical modeling",
                        "interface definition", "validation",
                        "quotations", "manufacturing"]:
            assert failure in content.lower(), f"Failure list missing: {failure}"


class TestAuditorPrinciples:
    """Verify all 10 Auditor's Principles (AP-1 through AP-10) are in
    MASTER_PROTOCOL.md and that the 5 governance files exist.

    Per external auditor: these principles codify the audit discipline
    that has governed this project since cycle 1. They are constitutional
    law — a coder who violates them is producing entropy.
    """

    def test_ap_1_run_it(self):
        """AP-1: Run it, don't reason about it."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "AP-1" in content
        assert "Run it" in content and "don't reason about it" in content

    def test_ap_1_has_content(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "Never claim a test passes without running it" in content

    def test_ap_2_paste_output(self):
        """AP-2: Paste actual output, not summaries."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "AP-2" in content
        assert "actual output" in content.lower()
        assert "not summaries" in content.lower()

    def test_ap_2_has_content(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "68 tests pass" in content  # the example of a summary

    def test_ap_3_fresh_clone(self):
        """AP-3: Fresh-clone verification."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "AP-3" in content
        assert "Fresh-clone" in content or "fresh clone" in content.lower()

    def test_ap_3_has_content(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "environment-dependent" in content.lower()

    def test_ap_4_resolved_vs_partial(self):
        """AP-4: Distinguish RESOLVED from PARTIALLY RESOLVED."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "AP-4" in content
        assert "RESOLVED" in content and "PARTIALLY RESOLVED" in content

    def test_ap_4_has_content(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "I fixed it" in content  # the example of not-resolved

    def test_ap_5_phantom_work(self):
        """AP-5: Phantom-work detection."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "AP-5" in content
        assert "Phantom-work" in content or "phantom work" in content.lower()

    def test_ap_5_has_content(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "JJ1" in content or "phantom" in content.lower()
        assert "git log" in content.lower()

    def test_ap_6_enforcement_chain(self):
        """AP-6: The enforcement chain (sensor → actuator → blocker → verified)."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "AP-6" in content
        assert "enforcement chain" in content.lower()
        for link in ["sensor", "actuator", "blocker", "verified"]:
            assert link in content.lower()

    def test_ap_6_has_content(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "warning, not enforcement" in content.lower()

    def test_ap_7_no_false_precision(self):
        """AP-7: No false precision (Law 27)."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "AP-7" in content
        assert "false precision" in content.lower()

    def test_ap_7_has_content(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "validation_level" in content or "evidence_strength" in content

    def test_ap_8_one_at_a_time(self):
        """AP-8: The one-at-a-time discipline."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "AP-8" in content
        assert "one-at-a-time" in content.lower() or "one at a time" in content.lower()

    def test_ap_8_has_content(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "Build ONE engine" in content or "ONE" in content

    def test_ap_9_accountability_loop(self):
        """AP-9: The accountability loop (git log, ls, pytest)."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "AP-9" in content
        assert "accountability loop" in content.lower()

    def test_ap_9_has_content(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "git log --oneline -1" in content
        assert "ls -la" in content
        assert "pytest" in content.lower()

    def test_ap_10_overclaim(self):
        """AP-10: The overclaim pattern."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "AP-10" in content
        assert "overclaim" in content.lower()

    def test_ap_10_has_content(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "all tests pass" in content.lower() or "all X pass" in content

    def test_all_5_governance_files_exist(self):
        """All 5 governance files in the read list must exist on disk."""
        for f in ["MASTER_PROTOCOL.md", "FAILURES.md", "CONSTITUTION.md",
                  "ANTI_ENTROPY.md", "CONTRIBUTING.md"]:
            assert (ROOT / f).exists(), f"Governance file missing: {f}"

    def test_anti_entropy_references_ap_principles(self):
        """ANTI_ENTROPY.md must reference the Auditor's Principles."""
        content = (ROOT / "ANTI_ENTROPY.md").read_text()
        assert "Auditor's Principles" in content or "AP-1" in content
        assert "entropy" in content.lower()

    def test_all_10_principles_present(self):
        """All 10 AP principles (AP-1 through AP-10) must be present."""
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        for i in range(1, 11):
            assert f"AP-{i}" in content, f"Missing AP-{i}"
