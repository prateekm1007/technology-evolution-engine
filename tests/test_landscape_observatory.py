"""Tests for landscape_observatory.py — cycle 222.

Auditor's update #12:
  - Landscape Observatory (logs every run)
  - Embedding classifier (replaces threshold boundaries)
  - Confidence classifier (probabilistic, sample-size aware)
"""
import sys
import math
import random
import tempfile
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


def test_observatory_imports():
    """Module imports cleanly."""
    from scripts.landscape_observatory import (
        LandscapeObservatory, ObservatoryEntry,
        EmbeddingClassifier, ConfidenceClassifier,
        landscape_to_embedding, embedding_distance,
    )
    assert LandscapeObservatory is not None
    assert EmbeddingClassifier is not None
    assert ConfidenceClassifier is not None


def test_observatory_logs_append_only():
    """Observatory logs are append-only (Law 7: Historical permanence)."""
    from scripts.landscape_observatory import LandscapeObservatory
    from scripts.meta_invention import LandscapeSignature, LandscapeType

    tmpdir = tempfile.mkdtemp()
    log_path = os.path.join(tmpdir, "test_obs.jsonl")
    obs = LandscapeObservatory(log_path=log_path)

    # Create a fake landscape signature
    sig = LandscapeSignature(
        n_samples=50, q25=0.1, q50=0.2, q75=0.3, q99=0.4, max_val=0.5,
        nonzero_fraction=0.8, skew_ratio=0.4, bimodality=0.3,
        interaction_index=0.4, landscape_type=LandscapeType.SMOOTH,
    )

    # Observe two runs
    obs.observe("test_domain", sig, "greedy_hill_climber",
                [{"iteration": 0, "best_outcome": 0.5},
                 {"iteration": 1, "best_outcome": 0.8}], seed=42, n_per_iter=50)
    obs.observe("test_domain", sig, "greedy_hill_climber",
                [{"iteration": 0, "best_outcome": 0.6},
                 {"iteration": 1, "best_outcome": 0.9}], seed=43, n_per_iter=50)

    assert len(obs.entries) == 2
    # Reload from disk — entries should persist
    obs2 = LandscapeObservatory(log_path=log_path)
    assert len(obs2.entries) == 2
    # Append-only: original entries are preserved
    assert obs2.entries[0].iter0_best == 0.5
    assert obs2.entries[1].iter0_best == 0.6


def test_observatory_records_convergence_and_regression():
    """Observatory records convergence_iter and regressed flag."""
    from scripts.landscape_observatory import LandscapeObservatory
    from scripts.meta_invention import LandscapeSignature, LandscapeType

    tmpdir = tempfile.mkdtemp()
    log_path = os.path.join(tmpdir, "test_obs.jsonl")
    obs = LandscapeObservatory(log_path=log_path)

    sig = LandscapeSignature(
        n_samples=50, q25=0.1, q50=0.2, q75=0.3, q99=0.4, max_val=0.5,
        nonzero_fraction=0.8, skew_ratio=0.4, bimodality=0.3,
        interaction_index=0.4, landscape_type=LandscapeType.SMOOTH,
    )

    # A run that regresses (iter5 < iter0)
    entry = obs.observe("test", sig, "bayesian_optimizer",
                        [{"iteration": 0, "best_outcome": 1.0},
                         {"iteration": 1, "best_outcome": 0.8},
                         {"iteration": 2, "best_outcome": 0.5}], seed=42, n_per_iter=50)
    assert entry.regressed is True
    assert entry.improvement == -0.5

    # A run that converges early
    entry2 = obs.observe("test", sig, "greedy_hill_climber",
                         [{"iteration": 0, "best_outcome": 0.5},
                          {"iteration": 1, "best_outcome": 1.0},
                          {"iteration": 2, "best_outcome": 1.0}], seed=42, n_per_iter=50)
    assert entry2.regressed is False
    assert entry2.convergence_iter <= 1  # reached 90% of final by iter 1


def test_embedding_is_domain_invariant():
    """Landscape embedding contains only statistical features, no domain info."""
    from scripts.landscape_observatory import landscape_to_embedding
    from scripts.meta_invention import LandscapeSignature, LandscapeType

    sig = LandscapeSignature(
        n_samples=50, q25=0.1, q50=0.2, q75=0.3, q99=0.4, max_val=0.5,
        nonzero_fraction=0.8, skew_ratio=0.4, bimodality=0.3,
        interaction_index=0.4, landscape_type=LandscapeType.SMOOTH,
    )
    emb = landscape_to_embedding(sig)
    assert isinstance(emb, list)
    assert len(emb) == 8  # 8 statistical features
    # All values should be in [0, 1] (normalized)
    for v in emb:
        assert 0.0 <= v <= 1.0, f"Embedding value {v} out of [0,1] range"


def test_embedding_distance():
    """Embedding distance is Euclidean and symmetric."""
    from scripts.landscape_observatory import embedding_distance

    e1 = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    e2 = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    assert embedding_distance(e1, e2) == 0.0  # identical

    e3 = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
    d1 = embedding_distance(e1, e3)
    d2 = embedding_distance(e3, e1)
    assert abs(d1 - d2) < 1e-9  # symmetric
    assert d1 > 0  # different


def test_confidence_classifier_returns_probabilities():
    """ConfidenceClassifier returns a probability distribution, not a single class."""
    from scripts.landscape_observatory import ConfidenceClassifier
    from scripts.synthetic_landscapes import SPHERE_DOMAIN, sphere_forward

    # Sample 100 candidates
    rng = random.Random(42)
    cands = []
    for _ in range(100):
        dp = {v["name"]: rng.uniform(*v["bounds"]) for v in SPHERE_DOMAIN["design_vars"]}
        o, _ = sphere_forward(dp)
        c = type("C", (), {"design_point": dp, "predicted_outcome": o, "derived": {}})()
        cands.append(c)

    classifier = ConfidenceClassifier(n_bootstrap=5)
    result = classifier.classify_with_confidence(cands, SPHERE_DOMAIN["design_vars"])

    assert "primary_type" in result
    assert "confidence" in result
    assert "type_distribution" in result
    assert 0.0 <= result["confidence"] <= 1.0
    # Type distribution should sum to ~1.0
    total = sum(result["type_distribution"].values())
    assert abs(total - 1.0) < 0.1  # allow for rounding


def test_confidence_classifier_reports_sample_size_sweep():
    """ConfidenceClassifier reports how confidence scales with sample size."""
    from scripts.landscape_observatory import ConfidenceClassifier
    from scripts.synthetic_landscapes import NEEDLE_DOMAIN, needle_forward

    rng = random.Random(42)
    cands = []
    for _ in range(100):
        dp = {v["name"]: rng.uniform(*v["bounds"]) for v in NEEDLE_DOMAIN["design_vars"]}
        o, _ = needle_forward(dp)
        c = type("C", (), {"design_point": dp, "predicted_outcome": o, "derived": {}})()
        cands.append(c)

    classifier = ConfidenceClassifier(n_bootstrap=5)
    result = classifier.classify_with_confidence(cands, NEEDLE_DOMAIN["design_vars"])

    assert "sample_size_sweep" in result
    assert len(result["sample_size_sweep"]) == 4  # 25%, 50%, 75%, 100%
    # Needle should have high confidence even with few samples
    # (it's far from classification boundaries)
    for n, conf, t in result["sample_size_sweep"]:
        assert 0.0 <= conf <= 1.0


def test_confidence_classifier_handles_insufficient_samples():
    """ConfidenceClassifier reports low confidence with <20 samples."""
    from scripts.landscape_observatory import ConfidenceClassifier
    from scripts.synthetic_landscapes import SPHERE_DOMAIN, sphere_forward

    rng = random.Random(42)
    cands = []
    for _ in range(10):  # only 10 samples
        dp = {v["name"]: rng.uniform(*v["bounds"]) for v in SPHERE_DOMAIN["design_vars"]}
        o, _ = sphere_forward(dp)
        c = type("C", (), {"design_point": dp, "predicted_outcome": o, "derived": {}})()
        cands.append(c)

    classifier = ConfidenceClassifier(n_bootstrap=5)
    result = classifier.classify_with_confidence(cands, SPHERE_DOMAIN["design_vars"])

    assert result["confidence"] == 0.0
    assert "Insufficient samples" in result.get("note", "")


def test_embedding_classifier_falls_back_when_observatory_empty():
    """EmbeddingClassifier falls back to threshold when observatory is empty."""
    from scripts.landscape_observatory import LandscapeObservatory, EmbeddingClassifier
    from scripts.synthetic_landscapes import SPHERE_DOMAIN, sphere_forward

    tmpdir = tempfile.mkdtemp()
    log_path = os.path.join(tmpdir, "empty_obs.jsonl")
    obs = LandscapeObservatory(log_path=log_path)
    assert len(obs.entries) == 0

    emb_classifier = EmbeddingClassifier(obs, k=5)

    rng = random.Random(42)
    cands = []
    for _ in range(50):
        dp = {v["name"]: rng.uniform(*v["bounds"]) for v in SPHERE_DOMAIN["design_vars"]}
        o, _ = sphere_forward(dp)
        c = type("C", (), {"design_point": dp, "predicted_outcome": o, "derived": {}})()
        cands.append(c)

    type_, conf, probs = emb_classifier.classify(cands, SPHERE_DOMAIN["design_vars"])
    # Should return a valid type (fallback to threshold)
    assert type_ is not None
    # Confidence should be low (no historical data)
    assert conf <= 0.5


def test_embedding_classifier_uses_historical_data():
    """EmbeddingClassifier uses historical data when available."""
    from scripts.landscape_observatory import LandscapeObservatory, EmbeddingClassifier
    from scripts.meta_invention import LandscapeSignature, LandscapeType, run_meta_invention
    from scripts.synthetic_landscapes import SPHERE_DOMAIN, sphere_forward, NEEDLE_DOMAIN, needle_forward

    tmpdir = tempfile.mkdtemp()
    log_path = os.path.join(tmpdir, "populated_obs.jsonl")
    obs = LandscapeObservatory(log_path=log_path)

    # Populate with a few runs
    for spec, fn in [(SPHERE_DOMAIN, sphere_forward), (NEEDLE_DOMAIN, needle_forward)]:
        iters, landscape, opt = run_meta_invention(spec, fn, n_iterations=3, n_per_iter=30, seed=42)
        obs.observe(spec["name"], landscape, opt, iters, seed=42, n_per_iter=30)

    emb_classifier = EmbeddingClassifier(obs, k=2)
    assert len(emb_classifier._historical_embeddings) >= 2

    # Classify a new sphere landscape
    rng = random.Random(99)
    cands = []
    for _ in range(50):
        dp = {v["name"]: rng.uniform(*v["bounds"]) for v in SPHERE_DOMAIN["design_vars"]}
        o, _ = sphere_forward(dp)
        c = type("C", (), {"design_point": dp, "predicted_outcome": o, "derived": {}})()
        cands.append(c)

    type_, conf, probs = emb_classifier.classify(cands, SPHERE_DOMAIN["design_vars"])
    # Should return a valid type and confidence > 0 (has historical data)
    assert type_ is not None
    assert conf > 0


def test_mechanistic_justification_renamed_honestly():
    """Cycle 222: 'executable causal chain' renamed to 'executable mechanistic
    justification' in user-facing prose. The class name CausalChain is kept
    for backward compatibility, but the docstring and printed labels are honest.
    """
    from scripts.meta_invention import CausalChain, CausalStep

    # Class still exists (backward compat)
    assert CausalChain is not None

    # Docstring should mention "mechanistic justification" (honest rename)
    assert "mechanistic justification" in CausalChain.__doc__.lower(), \
        "CausalChain docstring should mention 'mechanistic justification' per cycle 222 rename"
    # Docstring should be honest about curation
    assert "curated" in CausalChain.__doc__.lower() or "selected" in CausalChain.__doc__.lower(), \
        "CausalChain docstring should acknowledge it is curated/selected, not derived"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
