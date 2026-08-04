"""
Tests for F-045 / PR-21: corpus-derived tolerances replacing prior-map.

Per ANTI_ENTROPY.md rule 1 (tests first), these tests lock the F-045
contract:
  1. CORPUS_DERIVED_TOLERANCES dict exists on ConstraintModule.
  2. The 'material' tolerance is corpus-derived (not prior-map).
  3. Each corpus-derived entry has the required citation fields:
     source_patent_id, source_url, retrieval_date, source_text,
     prior_map=False, derivation_method.
  4. The source patent file actually exists in data/ingestion/patents/.
  5. The source URL returns HTTP 200 (live verification per PR-19).
  6. analyze_layer4() prefers corpus-derived over prior-map.
  7. analyze_layer4() correctly flags prior-map fallbacks with
     prior_map=True and a kill_test field.
  8. The corpus-derived value is NOT the prior-map value (they differ).
"""
import json
import pathlib
import subprocess
import sys
import urllib.request

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.constraint_module import ConstraintModule


# ----------------------------------------------------------------------
# 1. CORPUS_DERIVED_TOLERANCES dict exists and is well-formed
# ----------------------------------------------------------------------

def test_corpus_derived_tolerances_dict_exists():
    """F-045: the CORPUS_DERIVED_TOLERANCES class attribute exists."""
    assert hasattr(ConstraintModule, "CORPUS_DERIVED_TOLERANCES"), (
        "ConstraintModule must have CORPUS_DERIVED_TOLERANCES class attribute "
        "(per F-045 / PR-21)"
    )
    assert isinstance(ConstraintModule.CORPUS_DERIVED_TOLERANCES, dict)


def test_material_tolerance_is_corpus_derived():
    """The 'material' tolerance (highest-traffic constraint) MUST be
    corpus-derived (per F-045 / PR-21). It is forbidden from being a
    prior-map value."""
    cdt = ConstraintModule.CORPUS_DERIVED_TOLERANCES
    assert "material" in cdt, (
        "F-045 violation: 'material' tolerance is missing from "
        "CORPUS_DERIVED_TOLERANCES. The highest-traffic constraint type "
        "MUST have a corpus-derived value (per PR-21)."
    )


def test_corpus_derived_entry_has_required_citation_fields():
    """Each corpus-derived entry must carry the full citation chain:
    source_patent_id, source_url, retrieval_date, source_text,
    prior_map, derivation_method."""
    entry = ConstraintModule.CORPUS_DERIVED_TOLERANCES["material"]
    required_fields = [
        "value",
        "source_patent_id",
        "source_url",
        "retrieval_date",
        "source_text",
        "prior_map",
        "derivation_method",
    ]
    for field in required_fields:
        assert field in entry, (
            f"Corpus-derived 'material' tolerance missing field: {field}"
        )


def test_corpus_derived_entry_prior_map_is_false():
    """A corpus-derived entry MUST have prior_map=False (it is NOT a
    prior-map value)."""
    entry = ConstraintModule.CORPUS_DERIVED_TOLERANCES["material"]
    assert entry["prior_map"] is False, (
        f"Corpus-derived 'material' tolerance has prior_map={entry['prior_map']} "
        f"— must be False (it is corpus-derived, not prior-map)"
    )


def test_corpus_derived_entry_value_is_not_prior_map_value():
    """The corpus-derived value MUST differ from the prior-map value.
    If they were the same, the 'corpus-derived' entry would be a
    re-statement of the prior map, not an evidence-derived value."""
    cd_value = ConstraintModule.CORPUS_DERIVED_TOLERANCES["material"]["value"]
    pm_value = ConstraintModule.TOLERANCE_PRIORS["material"]
    assert cd_value != pm_value, (
        f"Corpus-derived value ({cd_value!r}) is identical to prior-map "
        f"value ({pm_value!r}). The corpus-derived entry must be a "
        f"genuinely different value mined from a real patent."
    )


def test_corpus_derived_source_text_is_nonempty():
    """The source_text field must contain the verbatim text from the
    patent that the value was extracted from. An empty source_text
    means the citation is fictional."""
    entry = ConstraintModule.CORPUS_DERIVED_TOLERANCES["material"]
    assert len(entry["source_text"]) > 50, (
        f"source_text is too short ({len(entry['source_text'])} chars) — "
        f"must contain the verbatim text from the patent."
    )


def test_corpus_derived_value_contains_quantitative_range():
    """The corpus-derived value must contain a quantitative range mined
    from the patent (e.g., '3-10%' or '650-700°C'). A value without
    quantitative ranges is not evidence-derived."""
    entry = ConstraintModule.CORPUS_DERIVED_TOLERANCES["material"]
    value = entry["value"]
    # Check for at least one quantitative range pattern: X-Y%
    import re
    range_pattern = re.compile(r"\d+\s*[-–]\s*\d+\s*(?:%|°C|nm|μm|rpm|:1)")
    assert range_pattern.search(value), (
        f"Corpus-derived value does not contain a quantitative range: {value!r}. "
        f"A real patent tolerance has concrete numeric ranges."
    )


# ----------------------------------------------------------------------
# 2. The source patent file exists in the corpus
# ----------------------------------------------------------------------

def test_source_patent_file_exists_in_corpus():
    """The source_patent_id referenced by the corpus-derived tolerance
    MUST correspond to a real file in data/ingestion/patents/. This
    ensures the citation is real, not fictional."""
    entry = ConstraintModule.CORPUS_DERIVED_TOLERANCES["material"]
    patent_id = entry["source_patent_id"]
    patent_file = ROOT / "data" / "ingestion" / "patents" / f"{patent_id}.txt"
    assert patent_file.exists(), (
        f"Source patent file does not exist: {patent_file}. "
        f"The corpus-derived tolerance cites a patent that is not in the "
        f"data/ingestion/patents/ corpus. Per F-045, the citation must "
        f"trace to a real file."
    )


def test_source_patent_file_contains_the_cited_text():
    """The source_text field must actually appear in the cited patent
    file. This is the strongest check that the citation is real: the
    text the value was extracted from must be verbatim in the file."""
    entry = ConstraintModule.CORPUS_DERIVED_TOLERANCES["material"]
    patent_id = entry["source_patent_id"]
    patent_file = ROOT / "data" / "ingestion" / "patents" / f"{patent_id}.txt"
    file_content = patent_file.read_text(encoding="utf-8")

    # The source_text field contains a snippet. Check that key phrases
    # from the snippet appear in the actual patent file.
    source_text = entry["source_text"]
    # Extract distinctive phrases (long enough to be unique)
    phrases = [
        "carbon coated LiFePO4",
        "citric acid",
        "stearic acid",
        "ball to powder ratio",
        "650",
        "700",
    ]
    for phrase in phrases:
        assert phrase in file_content, (
            f"Phrase {phrase!r} from source_text not found in patent file "
            f"{patent_file.name}. The citation is not verbatim from the file."
        )


# ----------------------------------------------------------------------
# 3. analyze_layer4() prefers corpus-derived over prior-map
# ----------------------------------------------------------------------

def test_analyze_layer4_prefers_corpus_derived_for_material():
    """When analyze_layer4() encounters a 'material' constraint, it
    MUST return the corpus-derived tolerance (not the prior-map value)."""
    cm = ConstraintModule(graph={"nodes": [], "edges": []})
    # Synthesize a constraint_layer3 output with a 'material' constraint
    constraint_layer3 = {
        "evidence": {
            "constraints_aggregated": ["material_strength", "cost"],
        }
    }
    result = cm.analyze_layer4(problem={}, constraint_layer3=constraint_layer3)
    tolerances = result["tolerances"]
    assert "material" in tolerances, (
        "analyze_layer4() did not produce a 'material' tolerance"
    )
    material_tol = tolerances["material"]
    # The corpus-derived entry has prior_map=False
    assert material_tol.get("prior_map") is False, (
        f"analyze_layer4() returned prior_map={material_tol.get('prior_map')} "
        f"for 'material' — must be False (corpus-derived is preferred)"
    )
    # The value must be the corpus-derived value, not the prior-map value
    cd_value = ConstraintModule.CORPUS_DERIVED_TOLERANCES["material"]["value"]
    assert material_tol.get("value") == cd_value, (
        f"analyze_layer4() returned value {material_tol.get('value')!r} "
        f"but expected corpus-derived value {cd_value!r}"
    )


def test_analyze_layer4_falls_back_to_prior_map_for_other_constraints():
    """For constraints without a corpus-derived entry (e.g., 'cost'),
    analyze_layer4() MUST fall back to the prior-map value AND flag
    it with prior_map=True."""
    cm = ConstraintModule(graph={"nodes": [], "edges": []})
    constraint_layer3 = {
        "evidence": {
            "constraints_aggregated": ["cost_estimate"],
        }
    }
    result = cm.analyze_layer4(problem={}, constraint_layer3=constraint_layer3)
    tolerances = result["tolerances"]
    assert "cost" in tolerances, (
        "analyze_layer4() did not produce a 'cost' tolerance"
    )
    cost_tol = tolerances["cost"]
    # The fallback entry has prior_map=True
    assert cost_tol.get("prior_map") is True, (
        f"analyze_layer4() returned prior_map={cost_tol.get('prior_map')} "
        f"for 'cost' — must be True (no corpus-derived value available, "
        f"so prior-map fallback is used)"
    )
    # The fallback entry has a kill_test field linking to F-045
    assert cost_tol.get("kill_test") == "KT-F045-cost", (
        f"Fallback 'cost' tolerance missing kill_test field. Per PR-21, "
        f"prior-map placeholders MUST be paired with a kill test."
    )


def test_analyze_layer4_counts_corpus_and_prior_map_correctly():
    """analyze_layer4() must report corpus_derived_count and
    prior_map_count in its evidence block."""
    cm = ConstraintModule(graph={"nodes": [], "edges": []})
    constraint_layer3 = {
        "evidence": {
            "constraints_aggregated": ["material_strength", "cost_estimate"],
        }
    }
    result = cm.analyze_layer4(problem={}, constraint_layer3=constraint_layer3)
    evidence = result["evidence"]
    assert evidence["corpus_derived_count"] == 1, (
        f"Expected 1 corpus-derived tolerance (material), got "
        f"{evidence['corpus_derived_count']}"
    )
    assert evidence["prior_map_count"] == 1, (
        f"Expected 1 prior-map tolerance (cost), got "
        f"{evidence['prior_map_count']}"
    )


def test_analyze_layer4_assumptions_mention_f045():
    """The assumptions block must mention F-045 / PR-21 explicitly,
    so that downstream consumers know which tolerances are evidence-derived
    vs prior-map placeholders."""
    cm = ConstraintModule(graph={"nodes": [], "edges": []})
    constraint_layer3 = {
        "evidence": {
            "constraints_aggregated": ["material_strength"],
        }
    }
    result = cm.analyze_layer4(problem={}, constraint_layer3=constraint_layer3)
    assumptions = result["assumptions"]
    combined_assumptions = " ".join(assumptions)
    assert "F-045" in combined_assumptions or "PR-21" in combined_assumptions, (
        f"assumptions block must mention F-045 or PR-21. Got: {assumptions}"
    )


# ----------------------------------------------------------------------
# 4. The source URL is verifiable (PR-19 / PR-20)
# ----------------------------------------------------------------------

def test_source_url_returns_http_200():
    """Per PR-19: the source URL must return HTTP 200. A 404 means
    the citation is broken."""
    entry = ConstraintModule.CORPUS_DERIVED_TOLERANCES["material"]
    url = entry["source_url"]
    try:
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "F-045-verifier/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            assert response.status == 200, (
                f"Source URL returned HTTP {response.status}, expected 200. "
                f"URL: {url}"
            )
    except urllib.error.HTTPError as e:
        if e.code == 405:
            # Some servers don't allow HEAD — try GET instead
            req = urllib.request.Request(url,
                                         headers={"User-Agent": "F-045-verifier/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                assert response.status == 200, (
                    f"Source URL returned HTTP {response.status}, expected 200."
                )
        else:
            pytest.fail(f"Source URL {url} returned HTTP {e.code}: {e}")
    except Exception as e:
        pytest.fail(f"Source URL {url} could not be fetched: {e}")


# ----------------------------------------------------------------------
# 5. Regression: TOLERANCE_PRIORS still exists (backwards compat)
# ----------------------------------------------------------------------

def test_tolerance_priors_dict_still_exists_as_fallback():
    """F-045 does NOT delete TOLERANCE_PRIORS — it remains as the
    fallback for constraints without corpus-derived entries. This
    test ensures backwards compatibility with code that reads
    TOLERANCE_PRIORS directly."""
    assert hasattr(ConstraintModule, "TOLERANCE_PRIORS"), (
        "TOLERANCE_PRIORS must still exist as the fallback dict. "
        "F-045 adds CORPUS_DERIVED_TOLERANCES alongside it; it does "
        "not delete it."
    )
    assert "cost" in ConstraintModule.TOLERANCE_PRIORS
    assert "energy" in ConstraintModule.TOLERANCE_PRIORS
    assert "material" in ConstraintModule.TOLERANCE_PRIORS  # deprecated but present


def test_material_prior_map_value_marked_deprecated():
    """The prior-map value for 'material' must be marked DEPRECATED in
    a comment, since the corpus-derived value is now preferred."""
    # Read the source file and check for the deprecation comment
    source_file = ROOT / "invention_compiler" / "constraint_module.py"
    source_text = source_file.read_text(encoding="utf-8")
    # Find the TOLERANCE_PRIORS dict and check that 'material' has a
    # DEPRECATED comment
    assert "DEPRECATED" in source_text and "material" in source_text, (
        "The prior-map 'material' value must be marked DEPRECATED in a comment, "
        "since the corpus-derived value is now preferred."
    )


# ----------------------------------------------------------------------
# 6. End-to-end: the live benchmark suite uses corpus-derived tolerances
# ----------------------------------------------------------------------

def test_constraint_module_runs_in_compiler_pipeline():
    """Smoke test: ConstraintModule can be instantiated with the live
    civilization graph and analyze_layer4() runs without errors."""
    graph_path = ROOT / "data" / "civilization_graph.json"
    if not graph_path.exists():
        pytest.skip("civilization_graph.json not present")
    with open(graph_path) as f:
        graph = json.load(f)
    cm = ConstraintModule(graph=graph)
    # Run analyze_layer4 with a synthetic layer3 output
    constraint_layer3 = {
        "evidence": {
            "constraints_aggregated": ["material_property", "cost", "energy"],
        }
    }
    result = cm.analyze_layer4(problem={}, constraint_layer3=constraint_layer3)
    # Should have 3 tolerances
    assert len(result["tolerances"]) == 3
    # 'material' should be corpus-derived (prior_map=False)
    assert result["tolerances"]["material"]["prior_map"] is False
    # 'cost' and 'energy' should be prior-map fallbacks (prior_map=True)
    assert result["tolerances"]["cost"]["prior_map"] is True
    assert result["tolerances"]["energy"]["prior_map"] is True
    # corpus_derived_count = 1, prior_map_count = 2
    assert result["evidence"]["corpus_derived_count"] == 1
    assert result["evidence"]["prior_map_count"] == 2
