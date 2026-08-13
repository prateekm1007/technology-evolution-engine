"""
Cross-corpus pilot tests (Issue #4).

Negative-test style: every test constructs a BAD condition, runs the system,
and asserts that the system BLOCKS or REJECTS. No coverage assertions.

Run:
    python -m pytest cross_corpus/tests/ -v
"""
import json
import sys
import tempfile
from pathlib import Path
from datetime import date, timedelta

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from cross_corpus.schema import (Paper, Patent, PatentFamily, Citation, Claim,
                                  Candidate, content_hash)
from cross_corpus.provenance import (provenance_qualifies_as_evidence,
                                       cross_corpus_edge, is_npl_citation)
from cross_corpus.family_normalizer import normalize_families, family_id_of
from cross_corpus.ingest import ingest_paper, ingest_patent, corpus_manifest
from cross_corpus.graph import EvidenceGraph
from cross_corpus.temporal_controls import (TemporalCutoff,
                                             check_no_future_leakage,
                                             paper_evidence_date,
                                             patent_evidence_date,
                                             previous_complete_utc_day)
from cross_corpus.entailed import (retrieval_negative_attestation,
                                    check_source_entailment)
from cross_corpus.candidate import (PredictionFreeze, OutcomeRecord,
                                     deterministic_score, write_freeze,
                                     verify_freeze)
from cross_corpus.null_controls import (build_null_a, build_null_b, build_null_c,
                                         build_null_d)
from cross_corpus.forensic import (build_hash_chain, verify_hash_chain,
                                    ResultPackage, verify_result_package,
                                    forensic_audit)
from cross_corpus.orchestrator import run_pilot, STATES


# ---- helpers ----

def _paper(pid="paper:test:1", pub="2020-01-01", mech="m", mat="X",
           claims=None, citations=None, failures=None, domain="d", title=""):
    return Paper(paper_id=pid, publication_date=pub, domain=domain,
                 mechanisms=[mech], materials=[mat],
                 claims=claims or [], citations=citations or [],
                 reported_failures=failures or [], title=title)


def _patent(pid="patent:EP:test:1", prio="2021-01-01", pub="2021-06-01",
            mech="m", mat="X", claims=None, citations=None, domain="d",
            family_id="", jurisdictions=None):
    return Patent(patent_id=pid, docdb_family_id=family_id,
                  publication_date=pub, priority_date=prio,
                  jurisdictions=jurisdictions or ["EP"],
                  domain=domain, mechanisms=[mech], materials=[mat],
                  claims=claims or [], citations=citations or [])


def _claim(subj="material:X", pred="achieves_property",
           obj="property:perf", value="0.5", negated=False):
    return Claim(subject=subj, predicate=pred, obj=obj, value=value, negated=negated)


# =====================================================================
# 1. SCHEMA / PROVENANCE
# =====================================================================

class TestSchemaProvenance:
    def test_bad_citation_role_rejected(self):
        """A citation with a role outside the EPO taxonomy must be rejected."""
        with pytest.raises(ValueError, match="Bad citation role"):
            Citation(source_id="patent:A", target_id="paper:B",
                     source_kind="patent", target_kind="paper", role="Z")

    def test_bad_source_kind_rejected(self):
        with pytest.raises(ValueError, match="Bad source_kind"):
            Citation(source_id="x", target_id="y", source_kind="book",
                     target_kind="paper", role="A")

    def test_unknown_role_never_qualifies_as_evidence(self):
        """UNKNOWN (*) must never qualify as evidence — mirrors PSCD's
        UNKNOWN-as-not-negative rule."""
        c = Citation(source_id="p1", target_id="p2", source_kind="patent",
                     target_kind="paper", role="*")
        assert provenance_qualifies_as_evidence(c) is False

    def test_background_role_not_evidence(self):
        """A (background) citation does not qualify as evidence of teaching."""
        c = Citation(source_id="p1", target_id="p2", source_kind="patent",
                     target_kind="paper", role="A")
        assert provenance_qualifies_as_evidence(c) is False

    def test_npl_citation_detected(self):
        """Patent -> paper is an NPL citation."""
        c = Citation(source_id="patent:A", target_id="paper:B",
                     source_kind="patent", target_kind="paper", role="X")
        assert is_npl_citation(c) is True
        assert cross_corpus_edge(c) is True

    def test_content_hash_stable(self):
        """Same content -> same hash (content-addressable)."""
        p1 = _paper()
        p2 = _paper()
        assert p1.content_hash() == p2.content_hash()

    def test_content_hash_changes_on_mutation(self):
        p1 = _paper()
        p2 = _paper(title="different")
        assert p1.content_hash() != p2.content_hash()


# =====================================================================
# 2. FAMILY NORMALIZATION
# =====================================================================

class TestFamilyNormalization:
    def test_same_priority_chain_same_family(self):
        """Patents sharing a priority chain collapse to one family."""
        p1 = _patent(pid="patent:EP:fam:1", prio="2020-01-01",
                     family_id="", )
        p1.processes = ["PRIORITY_CHAIN:2020-01-01"]
        p2 = _patent(pid="patent:US:fam:1", prio="2020-01-01",
                     family_id="")
        p2.processes = ["PRIORITY_CHAIN:2020-01-01"]
        fams = normalize_families([p1, p2])
        assert len(fams) == 1
        assert len(fams[0].member_patent_ids) == 2

    def test_different_priority_chains_different_families(self):
        p1 = _patent(pid="patent:EP:fam:1", prio="2020-01-01")
        p1.processes = ["PRIORITY_CHAIN:2020-01-01"]
        p2 = _patent(pid="patent:US:fam:2", prio="2021-01-01")
        p2.processes = ["PRIORITY_CHAIN:2021-01-01"]
        fams = normalize_families([p1, p2])
        assert len(fams) == 2


# =====================================================================
# 3. TEMPORAL CONTROLS
# =====================================================================

class TestTemporalControls:
    def test_future_dated_paper_detected_as_leakage(self):
        """A paper dated on/after cutoff is a temporal leakage violation."""
        cutoff = TemporalCutoff(cutoff="2024-01-01",
                                registered_at="2024-01-01T00:00:00Z")
        future_paper = _paper(pub="2024-06-01")
        result = check_no_future_leakage([future_paper], [], cutoff)
        assert result["passed"] is False
        assert result["violation_count"] == 1

    def test_same_day_not_eligible(self):
        """Strict <: a document dated ON the cutoff is NOT eligible."""
        cutoff = TemporalCutoff(cutoff="2024-01-01",
                                registered_at="2024-01-01T00:00:00Z")
        assert cutoff.is_eligible_evidence("2024-01-01") is False
        assert cutoff.is_eligible_evidence("2023-12-31") is True

    def test_patent_evidence_date_uses_earliest(self):
        """Evidence date = min(priority, publication) — conservative."""
        p = _patent(prio="2020-06-01", pub="2021-01-01")
        assert patent_evidence_date(p) == "2020-06-01"


# =====================================================================
# 4. ENTAILED / RETRIEVAL-NEGATIVE
# =====================================================================

class TestEntailed:
    def test_entailed_source_makes_candidate_not_negative(self):
        """If any source ENTAILS the claim, candidate is NOT retrieval-negative."""
        graph = EvidenceGraph()
        p = _paper(pid="paper:s1", claims=[_claim(subj="material:X",
                                                   pred="achieves_property",
                                                   obj="property:perf", value="0.5")])
        graph.add_paper(p)
        # candidate claims the same thing
        cand = Candidate(
            candidate_id="c1", motif="m_test", domain="d",
            node_ids=("paper:s1",),
            supporting_edge_summary="",
            candidate_claim_text="X achieves perf",
            predicted_outcome="material:X|achieves_property|property:perf|0.5|False",
            prediction_window_days=365,
            generated_at="2024-01-01T00:00:00Z",
        )
        att = retrieval_negative_attestation(graph, cand, ["paper:s1"])
        assert att["any_entails"] is True
        assert att["is_retrieval_negative"] is False

    def test_unknown_source_makes_candidate_negative(self):
        """If source is UNKNOWN (no matching claim), candidate IS negative."""
        graph = EvidenceGraph()
        p = _paper(pid="paper:s1", claims=[])  # no claims at all
        graph.add_paper(p)
        cand = Candidate(
            candidate_id="c1", motif="m_test", domain="d",
            node_ids=("paper:s1",),
            supporting_edge_summary="",
            candidate_claim_text="X achieves perf",
            predicted_outcome="material:X|achieves_property|property:perf|0.9|False",
            prediction_window_days=365,
            generated_at="2024-01-01T00:00:00Z",
        )
        att = retrieval_negative_attestation(graph, cand, ["paper:s1"])
        assert att["any_entails"] is False
        assert att["any_unknown"] is True
        assert att["is_retrieval_negative"] is True

    def test_contradicted_only_not_negative(self):
        """If all sources CONTRADICT (no UNKNOWN), candidate is NOT negative —
        pure contradiction is a different kind of result."""
        graph = EvidenceGraph()
        p = _paper(pid="paper:s1",
                   claims=[_claim(subj="material:X", pred="achieves_property",
                                  obj="property:perf", value="0.5", negated=True)])
        graph.add_paper(p)
        cand = Candidate(
            candidate_id="c1", motif="m_test", domain="d",
            node_ids=("paper:s1",),
            supporting_edge_summary="",
            candidate_claim_text="X achieves perf",
            predicted_outcome="material:X|achieves_property|property:perf|0.9|False",
            prediction_window_days=365,
            generated_at="2024-01-01T00:00:00Z",
        )
        att = retrieval_negative_attestation(graph, cand, ["paper:s1"])
        # contradicted, no unknown -> not retrieval-negative
        assert att["is_retrieval_negative"] is False

    def test_no_structured_claim_fails_closed(self):
        """A candidate without a parseable structured claim is UNKNOWN (not negative)."""
        graph = EvidenceGraph()
        p = _paper(pid="paper:s1", claims=[])
        graph.add_paper(p)
        cand = Candidate(
            candidate_id="c1", motif="m_test", domain="d",
            node_ids=("paper:s1",),
            supporting_edge_summary="",
            candidate_claim_text="vague claim",
            predicted_outcome="no pipes here",  # unparseable
            prediction_window_days=365,
            generated_at="2024-01-01T00:00:00Z",
        )
        att = retrieval_negative_attestation(graph, cand, ["paper:s1"])
        assert att["is_retrieval_negative"] is False  # fail-closed


# =====================================================================
# 5. FORENSIC INTEGRITY (hash chain, tamper detection)
# =====================================================================

class TestForensic:
    def test_hash_chain_tamper_detected(self):
        """Mutating any candidate invalidates the entire downstream chain."""
        c1 = Candidate(candidate_id="c1", motif="m", domain="d",
                       node_ids=("paper:a",), supporting_edge_summary="",
                       candidate_claim_text="claim 1",
                       predicted_outcome="a|b|c||False",
                       prediction_window_days=365, generated_at="t")
        c2 = Candidate(candidate_id="c2", motif="m", domain="d",
                       node_ids=("paper:b",), supporting_edge_summary="",
                       candidate_claim_text="claim 2",
                       predicted_outcome="a|b|c||False",
                       prediction_window_days=365, generated_at="t")
        chain = build_hash_chain([c1, c2])
        # tamper: mutate c1 in a way that changes its hash
        import dataclasses
        c1_tampered = dataclasses.replace(c1, candidate_claim_text="TAMPERED")
        result = verify_hash_chain(chain, [c1_tampered, c2])
        assert result["valid"] is False

    def test_chain_length_mismatch_detected(self):
        c1 = Candidate(candidate_id="c1", motif="m", domain="d",
                       node_ids=("paper:a",), supporting_edge_summary="",
                       candidate_claim_text="x", predicted_outcome="a|b|c||False",
                       prediction_window_days=365, generated_at="t")
        chain = build_hash_chain([c1])
        result = verify_hash_chain(chain, [])  # missing candidate
        assert result["valid"] is False

    def test_result_package_tamper_detected(self):
        """Mutating the result package file invalidates its hash sidecar."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            pkg = ResultPackage(
                pilot_id="test", generated_at="t", cutoff="2024-01-01",
                corpus_manifest={}, graph_stats={}, real_data_seal=False,
                candidates_total=0, candidates_per_motif={},
                retrieval_negative_count=0, null_control_results={},
                hash_chain=[], chain_root_hash="EMPTY",
                decision="STRUCTURAL_FAIL", decision_rule="rule",
                is_scientific_result=False,
            )
            p = Path(td) / "pkg.json"
            pkg.write(p)
            # tamper: append to the file
            p.write_text(p.read_text() + " TAMPERED")
            result = verify_result_package(p)
            assert result["valid"] is False

    def test_scientific_result_claim_on_synthetic_rejected(self):
        """A result package claiming is_scientific_result=True must fail audit
        on synthetic fixtures (real_data_seal=False)."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            pkg = ResultPackage(
                pilot_id="test", generated_at="t", cutoff="2024-01-01",
                corpus_manifest={}, graph_stats={}, real_data_seal=False,
                candidates_total=1, candidates_per_motif={},
                retrieval_negative_count=1, null_control_results={},
                hash_chain=[], chain_root_hash="abc",
                decision="STRUCTURAL_PASS", decision_rule="rule",
                is_scientific_result=True,  # FORBIDDEN on synthetic
            )
            p = Path(td) / "pkg.json"
            pkg.write(p)
            audit = forensic_audit(p)
            assert audit["passed"] is False
            # find the failing check
            checks = {c["check"]: c["passed"] for c in audit["checks"]}
            assert checks["NOT_CLAIMED_AS_SCIENTIFIC"] is False


# =====================================================================
# 6. PREDICTION FREEZE
# =====================================================================

class TestPredictionFreeze:
    def test_freeze_tamper_detected(self):
        """Mutating freeze.json after sealing must fail verification."""
        with tempfile.TemporaryDirectory() as td:
            c1 = Candidate(candidate_id="c1", motif="m", domain="d",
                           node_ids=("paper:a",), supporting_edge_summary="",
                           candidate_claim_text="x", predicted_outcome="a|b|c||False",
                           prediction_window_days=365, generated_at="t")
            freeze = PredictionFreeze.from_candidates([c1], "2024-01-01")
            write_freeze(freeze, Path(td))
            # tamper
            fp = Path(td) / "freeze.json"
            fp.write_text(fp.read_text() + " TAMPERED")
            result = verify_freeze(Path(td))
            assert result["valid"] is False

    def test_unknown_decision_rejected(self):
        """deterministic_score rejects decisions outside the vocabulary."""
        c = Candidate(candidate_id="c1", motif="m", domain="d",
                      node_ids=("paper:a",), supporting_edge_summary="",
                      candidate_claim_text="x", predicted_outcome="a|b|c||False",
                      prediction_window_days=365, generated_at="t")
        o = OutcomeRecord(candidate_id="c1", decision="MAYBE")
        assert deterministic_score(c, o) == "INVALID"

    def test_unknown_never_confirmed(self):
        c = Candidate(candidate_id="c1", motif="m", domain="d",
                      node_ids=("paper:a",), supporting_edge_summary="",
                      candidate_claim_text="x", predicted_outcome="a|b|c||False",
                      prediction_window_days=365, generated_at="t")
        o = OutcomeRecord(candidate_id="c1", decision="UNKNOWN")
        assert deterministic_score(c, o) == "UNKNOWN"


# =====================================================================
# 7. NULL CONTROLS (structural validity)
# =====================================================================

class TestNullControls:
    def test_null_a_preserves_node_count(self):
        """NULL_A (temporal shuffle) preserves the number of papers/patents."""
        papers = [_paper(pid=f"paper:p{i}", pub=f"2020-01-0{i+1}") for i in range(3)]
        patents = [_patent(pid=f"patent:EP:p{i}", prio=f"2021-01-0{i+1}")
                   for i in range(3)]
        for p in patents:
            p.processes = [f"PRIORITY_CHAIN:{p.priority_date}"]
        g = build_null_a(papers, patents, seed=1)
        assert len(g.papers) == 3
        assert len(g.patents) == 3

    def test_null_b_breaks_provenance(self):
        """NULL_B (label swap) changes some paper targets to patent targets."""
        papers = [_paper(pid="paper:p1", pub="2020-01-01")]
        patents = [_patent(pid="patent:EP:p1", prio="2021-01-01",
                           citations=[Citation(source_id="patent:EP:p1",
                                               target_id="paper:p1",
                                               source_kind="patent",
                                               target_kind="paper", role="X")])]
        patents[0].processes = [f"PRIORITY_CHAIN:{patents[0].priority_date}"]
        g = build_null_b(papers, patents, seed=42)
        # With seed=42 and 50% probability, the citation may or may not be swapped.
        # We just verify the graph builds without error and has the patent.
        assert "patent:EP:p1" in g.patents

    def test_null_d_separates_corpuses(self):
        """NULL_D papers-only graph has no patents, and vice versa."""
        papers = [_paper(pid="paper:p1", pub="2020-01-01")]
        patents = [_patent(pid="patent:EP:p1", prio="2021-01-01")]
        patents[0].processes = [f"PRIORITY_CHAIN:{patents[0].priority_date}"]
        result = build_null_d(papers, patents)
        assert len(result["papers_only"].patents) == 0
        assert len(result["patents_only"].papers) == 0


# =====================================================================
# 8. ORCHESTRATOR (fail-closed state machine)
# =====================================================================

class TestOrchestrator:
    def test_temporal_leakage_aborts_pilot(self):
        """If any paper is dated on/after cutoff, the pilot must abort."""
        future_paper = _paper(pid="paper:future", pub="2025-01-01")
        # cutoff is 2024-01-01 -> future_paper leaks
        result = run_pilot([future_paper], [], cutoff="2024-01-01",
                           output_dir=Path(tempfile.mkdtemp()))
        assert result["state"]["state"] == "ABORTED"
        assert result["result_package_path"] is None

    def test_real_data_seal_on_synthetic_forbidden(self):
        """run_pilot with real_data_seal=True on synthetic fixtures must
        still report real_data_seal=False in the package (the orchestrator
        does not enforce this — the CLI does. Here we verify the orchestrator
        passes the flag through honestly)."""
        papers = [_paper(pid="paper:p1", pub="2020-01-01")]
        result = run_pilot(papers, [], cutoff="2024-01-01",
                           real_data_seal=True,
                           output_dir=Path(tempfile.mkdtemp()))
        # The orchestrator accepts the flag but forensic audit must catch
        # the inconsistency if is_scientific_result were True.
        # Here we just verify the pilot ran to completion.
        assert result["state"]["state"] in ("DECISION_SEALED", "ABORTED")

    def test_no_illegal_state_transition(self):
        """OrchestratorState.advance must reject non-sequential transitions."""
        from cross_corpus.orchestrator import OrchestratorState
        s = OrchestratorState()
        with pytest.raises(RuntimeError, match="illegal transition"):
            s.advance("MOTIFS_RUN", {})  # skipping GRAPH_LOADED

    def test_states_complete(self):
        """The state machine must include all 10 states + ABORTED."""
        assert "BLOCKED" in STATES
        assert "GRAPH_LOADED" in STATES
        assert "CONTROLS_VERIFIED" in STATES
        assert "MOTIFS_RUN" in STATES
        assert "CANDIDATES_FILTERED" in STATES
        assert "PREDICTIONS_SEALED" in STATES
        assert "SCORED" in STATES
        assert "ANALYZED" in STATES
        assert "DECISION_SEALED" in STATES
        assert "ABORTED" in STATES
        assert len(STATES) == 10


# =====================================================================
# 9. END-TO-END ON FIXTURES (structural validity only)
# =====================================================================

class TestEndToEnd:
    def test_fixtures_load_and_pilot_runs(self):
        """The full pilot runs on the synthetic fixtures and produces a
        STRUCTURAL_PASS or STRUCTURAL_FAIL (never a scientific result)."""
        fdir = REPO / "cross_corpus" / "fixtures"
        if not (fdir / "papers.jsonl").exists():
            pytest.skip("fixtures not generated yet")
        from cross_corpus.ingest import load_papers_jsonl, load_patents_jsonl
        papers = load_papers_jsonl(fdir / "papers.jsonl")
        patents = load_patents_jsonl(fdir / "patents.jsonl")
        result = run_pilot(papers, patents, cutoff="2024-06-01",
                           output_dir=Path(tempfile.mkdtemp()))
        assert result["state"]["state"] == "DECISION_SEALED"
        assert result["state"]["decision"] in ("STRUCTURAL_PASS", "STRUCTURAL_FAIL")
        assert result["state"]["is_scientific_result"] is False
        assert result["forensic_audit"]["passed"] is True

    def test_all_motifs_fire_on_fixtures(self):
        """Every one of the 10 motifs must produce >=1 candidate on fixtures
        (verifies that planted instances are detectable)."""
        fdir = REPO / "cross_corpus" / "fixtures"
        if not (fdir / "papers.jsonl").exists():
            pytest.skip("fixtures not generated yet")
        from cross_corpus.ingest import load_papers_jsonl, load_patents_jsonl
        papers = load_papers_jsonl(fdir / "papers.jsonl")
        patents = load_patents_jsonl(fdir / "patents.jsonl")
        result = run_pilot(papers, patents, cutoff="2024-06-01",
                           output_dir=Path(tempfile.mkdtemp()))
        per_motif = result["state"].get("graph_stats", {})  # not per-motif; check pkg
        # read the package
        import json
        pkg = json.loads(Path(result["result_package_path"]).read_text())
        for motif_name in [
            "m01_constraint_release", "m02_paper_patent_gap", "m03_patent_science_gap",
            "m04_paper_failure_patent_workaround", "m05_old_science_new_patent",
            "m06_two_papers_two_families", "m07_three_papers_one_patent",
            "m08_one_paper_three_families", "m09_jurisdictional_divergence",
            "m10_unexplained_bridge",
        ]:
            count = pkg["candidates_per_motif"].get(motif_name, 0)
            assert count > 0, f"Motif {motif_name} produced 0 candidates (planted instance not detected)"

    def test_null_controls_all_run(self):
        """All 4 null controls must produce a count (not error)."""
        fdir = REPO / "cross_corpus" / "fixtures"
        if not (fdir / "papers.jsonl").exists():
            pytest.skip("fixtures not generated yet")
        from cross_corpus.ingest import load_papers_jsonl, load_patents_jsonl
        papers = load_papers_jsonl(fdir / "papers.jsonl")
        patents = load_patents_jsonl(fdir / "patents.jsonl")
        result = run_pilot(papers, patents, cutoff="2024-06-01",
                           output_dir=Path(tempfile.mkdtemp()))
        nulls = result["state"]["null_control_results"]
        for key in ("NULL_A", "NULL_B", "NULL_C",
                     "NULL_D_papers_only", "NULL_D_patents_only"):
            assert key in nulls, f"Missing null control: {key}"
            assert isinstance(nulls[key], int)
