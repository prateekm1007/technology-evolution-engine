"""Tests for tee_full_pipeline.py — the 15-step TEE pipeline."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_pipeline_importable():
    """The full pipeline is importable."""
    from scripts.tee_full_pipeline import run_full_pipeline, DocumentPipelineResult
    assert run_full_pipeline is not None
    assert DocumentPipelineResult is not None


def test_pipeline_runs_on_document():
    """The pipeline runs on a corpus document and produces all 15 steps."""
    from scripts.tee_full_pipeline import run_full_pipeline
    from scripts.nlp_pipeline import NLPPipeline
    pipeline = NLPPipeline()
    doc = Path(__file__).resolve().parents[1] / "data" / "ingestion" / "corpus_50x" / "1012.0721v1.txt"
    result = run_full_pipeline(doc, pipeline)

    # Provenance (DR-43 required fields)
    assert result.provenance["source_id"] != ""
    assert result.provenance["provenance_hash"] != ""
    assert result.provenance["publication_date"] != ""
    assert result.provenance["prediction_lock_time"] != ""

    # All 15 steps produce output
    assert isinstance(result.entities, list)
    assert isinstance(result.relations, list)
    assert isinstance(result.mechanisms, list)
    assert isinstance(result.constraints, list)
    assert isinstance(result.contradictions, list)
    assert isinstance(result.governing_laws, list)
    assert isinstance(result.missing_prerequisites, list)
    assert isinstance(result.cross_domain_analogies, list)
    assert isinstance(result.candidate_interventions, list)
    assert isinstance(result.uncertainty_estimates, dict)
    assert isinstance(result.alternative_hypotheses, list)
    assert isinstance(result.counterexamples, list)
    assert isinstance(result.falsification_experiments, list)
    assert isinstance(result.locked_predictions, list)
    assert isinstance(result.reaudit_results, dict)

    # Re-audit produces a verdict
    assert result.reaudit_results.get("verdict") in ("UPHELD", "OVERTURNED", "UNRESOLVED")

    # Confidence is in [0, 1]
    assert 0.0 <= result.confidence <= 1.0

    # Failure modes are reported honestly
    assert isinstance(result.failure_modes, list)
    assert isinstance(result.unresolved_questions, list)


def test_pipeline_provenance_hash():
    """The provenance hash is deterministic for the same document."""
    from scripts.tee_full_pipeline import run_full_pipeline
    from scripts.nlp_pipeline import NLPPipeline
    pipeline = NLPPipeline()
    doc = Path(__file__).resolve().parents[1] / "data" / "ingestion" / "corpus_50x" / "0905.4191v2.txt"
    r1 = run_full_pipeline(doc, pipeline)
    r2 = run_full_pipeline(doc, pipeline)
    assert r1.provenance["provenance_hash"] == r2.provenance["provenance_hash"]


def test_pipeline_reaudit_independence():
    """The re-audit uses independent vocabulary (different hash)."""
    from scripts.tee_full_pipeline import run_full_pipeline
    from scripts.nlp_pipeline import NLPPipeline
    pipeline = NLPPipeline()
    doc = Path(__file__).resolve().parents[1] / "data" / "ingestion" / "corpus_50x" / "1007.5399v1.txt"
    result = run_full_pipeline(doc, pipeline)
    # The re-audit vocab hash must differ from the original
    assert result.reaudit_results["original_vocab_hash"] != result.reaudit_results["reaudit_vocab_hash"]


def test_pipeline_locked_predictions():
    """Locked predictions have a lock timestamp and provenance hash."""
    from scripts.tee_full_pipeline import run_full_pipeline
    from scripts.nlp_pipeline import NLPPipeline
    pipeline = NLPPipeline()
    doc = Path(__file__).resolve().parents[1] / "data" / "ingestion" / "corpus_50x" / "1012.0721v1.txt"
    result = run_full_pipeline(doc, pipeline)
    for pred in result.locked_predictions:
        assert "locked_at" in pred
        assert "provenance_hash" in pred
        assert "prediction" in pred


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
