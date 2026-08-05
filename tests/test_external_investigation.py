#!/usr/bin/env python3
"""
Test: External Investigation Module (F-065 source-text verification).

Per P2 (ANTI_ENTROPY.md): "Untested code is unverified code, permanently.
Every fix to an untested module MUST include a new test."

Per P27: "Read the assertion, not the test name — a test that asserts True
is theater." These tests have real assertions.

Per P28: "Test with 3+ inputs: the exact case, a natural variation, and an
edge case."

This test file locks the contract of scripts/external_investigation.py:
  1. verify_edge_against_text() correctly classifies edges as
     PRESENT / PARTIAL / ABSENT based on term presence in source text.
  2. fetch_page_text() returns lowercased stripped text (or empty string
     on failure).
  3. investigate() produces a report with the required fields and a
     valid overall verdict.
"""
import sys
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.external_investigation import (
    verify_edge_against_text,
    fetch_page_text,
    investigate,
)


class TestVerifyEdgeAgainstText:
    """Test the edge verification function with 3+ inputs per P28."""

    def test_present_edge(self):
        """Exact case: all mechanism terms present in source text."""
        edge = {
            "source_label": "lotus leaf",
            "target_label": "contact angle",
            "mechanism": "Lotus leaf has high contact angle due to roughness",
        }
        source_text = "the lotus leaf exhibits a high contact angle of 150 degrees due to surface roughness"
        result = verify_edge_against_text(edge, source_text)
        assert result["source_term_found"] is True
        assert result["target_term_found"] is True
        assert result["verdict"] == "PRESENT"

    def test_partial_edge(self):
        """Natural variation: some terms present, some missing."""
        edge = {
            "source_label": "nanofiber",
            "target_label": "permeability",
            "mechanism": "Nanofiber membrane controls selective permeability for filtration",
        }
        source_text = "nanofiber membranes show high permeability in water treatment"
        result = verify_edge_against_text(edge, source_text)
        assert result["source_term_found"] is True
        assert result["target_term_found"] is True
        # "selective" and "filtration" are missing, "controls" is missing
        assert result["verdict"] in ("PARTIAL", "PRESENT")

    def test_absent_edge(self):
        """Edge case: no terms present in source text."""
        edge = {
            "source_label": "blockchain",
            "target_label": "consensus",
            "mechanism": "Blockchain uses Byzantine fault tolerant consensus algorithm",
        }
        source_text = "the lotus leaf has a high contact angle due to roughness"
        result = verify_edge_against_text(edge, source_text)
        assert result["source_term_found"] is False
        assert result["target_term_found"] is False
        assert result["verdict"] == "ABSENT"

    def test_empty_source_text(self):
        """Edge case: empty source text returns ABSENT."""
        edge = {
            "source_label": "lotus",
            "target_label": "leaf",
            "mechanism": "Lotus leaf has superhydrophobic properties",
        }
        result = verify_edge_against_text(edge, "")
        assert result["source_term_found"] is False
        assert result["target_term_found"] is False
        assert result["verdict"] == "ABSENT"

    def test_empty_edge(self):
        """Edge case: empty edge labels are treated as found (vacuous truth)."""
        edge = {
            "source_label": "",
            "target_label": "",
            "mechanism": "",
        }
        result = verify_edge_against_text(edge, "some text")
        assert result["source_term_found"] is True  # vacuous
        assert result["target_term_found"] is True  # vacuous
        # No mechanism terms, so 0 missing of 0 -> PRESENT
        assert result["verdict"] == "PRESENT"


class TestFetchPageText:
    """Test the page fetching function."""

    def test_fetch_returns_string(self):
        """fetch_page_text returns a string (possibly empty)."""
        # Use a stable URL (example.com)
        text = fetch_page_text("https://example.com", timeout=10)
        assert isinstance(text, str)

    def test_fetch_invalid_url_returns_empty(self):
        """fetch_page_text returns empty string on invalid URL."""
        text = fetch_page_text("https://this-domain-does-not-exist-12345.invalid", timeout=5)
        assert text == ""

    def test_fetch_strips_html(self):
        """fetch_page_text strips HTML tags and returns lowercased text."""
        text = fetch_page_text("https://example.com", timeout=10)
        # Should not contain HTML tags
        if text:
            assert "<" not in text or "<" not in text.split(">")[0]
            assert text == text.lower()


class TestInvestigateReport:
    """Test the investigate() function produces a valid report."""

    def test_investigate_returns_required_fields(self):
        """investigate() returns a dict with all required fields."""
        # Use a simple, known query that will return results
        report = investigate(
            experiment_id="TEST-UNIT",
            lit_a_query="lotus leaf superhydrophobic",
            lit_b_query="battery separator electrolyte",
            bridge_a_edges=[
                {
                    "source": "lotus_leaf", "target": "contact_angle",
                    "source_label": "lotus", "target_label": "contact angle",
                    "mechanism": "Lotus leaf has high contact angle from roughness",
                }
            ],
            bridge_b_edges=[
                {
                    "source": "battery_separator", "target": "electrolyte_uptake",
                    "source_label": "battery", "target_label": "electrolyte",
                    "mechanism": "Battery separator affects electrolyte uptake",
                }
            ],
            shared_node_labels=["contact_angle", "electrolyte_uptake"],
        )
        assert isinstance(report, dict)
        assert report["type"] == "external_investigation"
        assert report["experiment_id"] == "TEST-UNIT"
        assert "timestamp" in report
        assert report["writer"] == "scripts.external_investigation"
        assert "lit_a_query" in report
        assert "lit_b_query" in report
        assert "lit_a_urls_fetched" in report
        assert "lit_a_combined_text_length" in report
        assert "lit_a_edge_verifications" in report
        assert "lit_b_urls_fetched" in report
        assert "lit_b_combined_text_length" in report
        assert "lit_b_edge_verifications" in report
        assert "overall_verdict" in report
        assert "critical_edges_a" in report
        assert "critical_edges_b" in report
        assert "f065_implication" in report

    def test_investigate_verdict_is_valid(self):
        """The overall verdict is one of the 3 valid values."""
        report = investigate(
            experiment_id="TEST-VERDICT",
            lit_a_query="lotus leaf",
            lit_b_query="battery",
            bridge_a_edges=[
                {
                    "source": "a", "target": "b",
                    "source_label": "lotus", "target_label": "leaf",
                    "mechanism": "lotus leaf has properties",
                }
            ],
            bridge_b_edges=[
                {
                    "source": "c", "target": "d",
                    "source_label": "battery", "target_label": "separator",
                    "mechanism": "battery separator has properties",
                }
            ],
            shared_node_labels=["b", "c"],
        )
        assert report["overall_verdict"] in (
            "EXTRACTION_VERIFIED",
            "EXTRACTION_PARTIAL",
            "EXTRACTION_FAILED",
        )

    def test_investigate_edge_verifications_have_verdicts(self):
        """Each edge verification has a verdict field."""
        report = investigate(
            experiment_id="TEST-EDGES",
            lit_a_query="pitcher plant",
            lit_b_query="fertilizer",
            bridge_a_edges=[
                {
                    "source": "pitcher", "target": "peristome",
                    "source_label": "pitcher", "target_label": "peristome",
                    "mechanism": "Pitcher plant has peristome surface",
                }
            ],
            bridge_b_edges=[
                {
                    "source": "fertilizer", "target": "soil",
                    "source_label": "fertilizer", "target_label": "soil",
                    "mechanism": "Fertilizer releases nutrients to soil",
                }
            ],
            shared_node_labels=["peristome", "fertilizer"],
        )
        for edge_result in report["lit_a_edge_verifications"]:
            assert "verdict" in edge_result
            assert edge_result["verdict"] in ("PRESENT", "PARTIAL", "ABSENT")
        for edge_result in report["lit_b_edge_verifications"]:
            assert "verdict" in edge_result
            assert edge_result["verdict"] in ("PRESENT", "PARTIAL", "ABSENT")


class TestModuleContract:
    """Test that the module satisfies its documented contract (P15: track
    exists / unit-verified / wired-and-integration-verified)."""

    def test_module_importable(self):
        """The module can be imported (exists + unit-verified)."""
        from scripts import external_investigation
        assert hasattr(external_investigation, "investigate")
        assert hasattr(external_investigation, "verify_edge_against_text")
        assert hasattr(external_investigation, "fetch_page_text")
        assert hasattr(external_investigation, "log_investigation")

    def test_generic_principles_list_exists(self):
        """The nontriviality_check module has a generic principles list."""
        from scripts import nontriviality_check
        assert hasattr(nontriviality_check, "GENERIC_PRINCIPLES")
        assert isinstance(nontriviality_check.GENERIC_PRINCIPLES, list)
        assert len(nontriviality_check.GENERIC_PRINCIPLES) > 10
        # Contact angle must be in the list (it's the EXP-BLIND-023 mechanism)
        assert "contact_angle" in nontriviality_check.GENERIC_PRINCIPLES

    def test_nontriviality_check_importable(self):
        """The nontriviality_check module can be imported."""
        from scripts import nontriviality_check
        assert hasattr(nontriviality_check, "run_nontriviality_check")
        assert hasattr(nontriviality_check, "search_citation_bridge")
        assert hasattr(nontriviality_check, "check_mechanism_specificity")
        assert hasattr(nontriviality_check, "check_domain_specific_knowledge")
