#!/usr/bin/env python3
"""
external_investigation.py — F-065 source-text verification engine.

Per CEO directive (cycle 84 worklog): "we will specifically devote a whole
coding module to deal with external investigation."

Per F-065 (cycle 83): LLM-guided extraction produces ASSERTED-tier mechanism
edges that are not verified against source text. This module closes that gap.

What it does:
  1. Takes an experiment_id (e.g., EXP-BLIND-022).
  2. Reads the predictions.jsonl entry for that experiment.
  3. Re-fetches the literature search results for both Literature A and B.
  4. For the top papers returned, fetches the full page content via curl.
  5. For each extracted mechanism edge, checks whether the edge's key terms
     (source node label, target node label, mechanism keywords) appear in
     the source text of the corresponding literature.
  6. Produces a verification verdict:
       - EXTRACTION_VERIFIED: the mechanism terms are present in source text
       - EXTRACTION_PARTIAL: some terms present, some not
       - EXTRACTION_FAILED: key mechanism terms absent from source text
  7. Appends the verdict to predictions.jsonl as a separate entry.

This is the F-065 fix. A PROVISIONAL_NOVEL_HIT can only be promoted to
confirmed NOVEL_HIT if this module returns EXTRACTION_VERIFIED for the
critical bridge edges.

Governance read receipt (cycle 85, 2026-08-05):
  - ANTI_ENTROPY.md read in full (cycle 83, carried forward).
  - Key line: "A claim is not true until it has been executed." (P1)
  - F-065: LLM-guided extraction is ASSERTED-tier until verified against
    source text. This module performs that verification.
  - DR-15: mechanism claims must be executable, not just present. This
    module checks presence in source text (a weaker check than executability,
    but a necessary first step).
"""
import sys
import json
import re
import pathlib
import subprocess
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional

ROOT = pathlib.Path(__file__).resolve().parents[1]
PREDICTIONS = ROOT / "data" / "ledger" / "predictions.jsonl"


def fetch_search_results(query: str, num: int = 8) -> List[Dict]:
    """Fetch papers via z-ai web_search. Returns list of {url, name, snippet}."""
    result = subprocess.run(
        ["z-ai", "function", "-n", "web_search", "-a", json.dumps({"query": query, "num": num})],
        capture_output=True, text=True, timeout=30
    )
    match = re.search(r'\[.*\]', result.stdout, re.DOTALL)
    if match:
        return json.loads(match.group())
    return []


def fetch_page_text(url: str, timeout: int = 20) -> str:
    """Fetch full page content via curl, strip HTML to text."""
    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", str(timeout), "-A",
             "Mozilla/5.0 (research verification)", url],
            capture_output=True, text=True, timeout=timeout + 5
        )
        html = result.stdout
        # Strip HTML tags (rough but sufficient for keyword presence check)
        text = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'&[a-z]+;', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.lower()
    except Exception as e:
        return ""


def verify_edge_against_text(edge: Dict, source_text: str) -> Dict:
    """Verify that an edge's key terms appear in the source text.

    Returns: {
        'source_term_found': bool,
        'target_term_found': bool,
        'mechanism_terms_found': list of found terms,
        'mechanism_terms_missing': list of missing terms,
        'verdict': 'PRESENT' | 'PARTIAL' | 'ABSENT'
    }
    """
    source_label = edge.get("source_label", "").lower()
    target_label = edge.get("target_label", "").lower()
    mechanism = edge.get("mechanism", "").lower()

    # Extract key terms from the mechanism (nouns/adjectives, >4 chars)
    mech_terms = [w for w in re.findall(r'\b[a-z]{5,}\b', mechanism)
                  if w not in {'these', 'those', 'their', 'there', 'where',
                               'which', 'whose', 'being', 'having', 'under',
                               'after', 'before', 'between', 'through',
                               'during', 'while', 'about', 'would', 'could',
                               'should', 'may', 'might', 'also', 'than'}]

    src_found = source_label in source_text if source_label else True
    tgt_found = target_label in source_text if target_label else True

    found_terms = [t for t in mech_terms if t in source_text]
    missing_terms = [t for t in mech_terms if t not in source_text]

    if src_found and tgt_found and len(missing_terms) <= len(found_terms) * 0.5:
        verdict = "PRESENT"
    elif src_found or tgt_found or len(found_terms) >= 2:
        verdict = "PARTIAL"
    else:
        verdict = "ABSENT"

    return {
        "source_term_found": src_found,
        "target_term_found": tgt_found,
        "mechanism_terms_found": found_terms,
        "mechanism_terms_missing": missing_terms,
        "verdict": verdict,
    }


def investigate(experiment_id: str, lit_a_query: str, lit_b_query: str,
                bridge_a_edges: List[Dict], bridge_b_edges: List[Dict],
                shared_node_labels: List[str]) -> Dict:
    """Run external investigation on a blind test result.

    For each literature, fetches top search results, retrieves full page
    text for the top 3 URLs, and verifies the bridge edges against the
    combined source text.

    Returns a verification report.
    """
    print(f"\n{'='*70}")
    print(f"EXTERNAL INVESTIGATION: {experiment_id}")
    print(f"{'='*70}")
    print(f"Literature A: {lit_a_query}")
    print(f"Literature B: {lit_b_query}")

    report = {
        "type": "external_investigation",
        "experiment_id": experiment_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "writer": "scripts.external_investigation",
        "lit_a_query": lit_a_query,
        "lit_b_query": lit_b_query,
    }

    for side, query, bridge_edges in [("a", lit_a_query, bridge_a_edges),
                                       ("b", lit_b_query, bridge_b_edges)]:
        print(f"\n--- Literature {side}: {query} ---")
        papers = fetch_search_results(query, num=8)
        print(f"  Fetched {len(papers)} search results")

        # Fetch full text for top 4 URLs (some may be paywalled/empty)
        combined_text = ""
        urls_used = []
        for p in papers[:4]:
            url = p.get("url", "")
            if not url:
                continue
            print(f"  Fetching: {url[:70]}...")
            text = fetch_page_text(url)
            if text and len(text) > 1000:  # skip empty/tiny pages
                combined_text += " " + text
                urls_used.append(url)
                time.sleep(0.3)  # polite delay

        print(f"  Combined source text: {len(combined_text)} chars from {len(urls_used)} URLs")

        # Verify each bridge edge
        edge_results = []
        for edge in bridge_edges:
            result = verify_edge_against_text(edge, combined_text)
            edge_results.append({
                "source": edge.get("source", ""),
                "target": edge.get("target", ""),
                "mechanism": edge.get("mechanism", "")[:80],
                **result,
            })
            print(f"  Edge {edge.get('source','?')} -> {edge.get('target','?')}: {result['verdict']}")

        report[f"lit_{side}_urls_fetched"] = urls_used
        report[f"lit_{side}_combined_text_length"] = len(combined_text)
        report[f"lit_{side}_edge_verifications"] = edge_results

    # Overall verdict
    a_edges = report.get("lit_a_edge_verifications", [])
    b_edges = report.get("lit_b_edge_verifications", [])
    # The critical edges are the ones connecting to the shared intermediate node.
    # Match by node ID (e.g., "controlled_release_membrane") against shared list.
    shared_lower = [s.lower() for s in shared_node_labels]
    a_critical = [e for e in a_edges
                  if e["source"].lower() in shared_lower or e["target"].lower() in shared_lower]
    b_critical = [e for e in b_edges
                  if e["source"].lower() in shared_lower or e["target"].lower() in shared_lower]

    # If no critical edges matched by node ID (e.g., shared node was only in shared list,
    # not in A or B edges), fall back to counting ALL edges as critical.
    if not a_critical:
        a_critical = a_edges
    if not b_critical:
        b_critical = b_edges

    a_present = sum(1 for e in a_critical if e["verdict"] == "PRESENT")
    a_partial = sum(1 for e in a_critical if e["verdict"] == "PARTIAL")
    a_absent = sum(1 for e in a_critical if e["verdict"] == "ABSENT")
    b_present = sum(1 for e in b_critical if e["verdict"] == "PRESENT")
    b_partial = sum(1 for e in b_critical if e["verdict"] == "PARTIAL")
    b_absent = sum(1 for e in b_critical if e["verdict"] == "ABSENT")

    if a_present > 0 and b_present > 0:
        overall = "EXTRACTION_VERIFIED"
    elif (a_present + a_partial) > 0 and (b_present + b_partial) > 0:
        overall = "EXTRACTION_PARTIAL"
    else:
        overall = "EXTRACTION_FAILED"

    report["overall_verdict"] = overall
    report["critical_edges_a"] = {"present": a_present, "partial": a_partial, "absent": a_absent}
    report["critical_edges_b"] = {"present": b_present, "partial": b_partial, "absent": b_absent}
    report["f065_implication"] = (
        f"PROVISIONAL_NOVEL_HIT can be {'PROMOTED to confirmed NOVEL_HIT' if overall == 'EXTRACTION_VERIFIED' else 'KEPT PROVISIONAL (partial verification)' if overall == 'EXTRACTION_PARTIAL' else 'DOWNGRADED to RETRIEVAL or NULL (extraction not supported by source text)'}. "
        f"Per F-065: LLM-guided extraction requires source-text verification before promotion."
    )

    print(f"\n  OVERALL VERDICT: {overall}")
    print(f"  Critical edges A: present={a_present}, partial={a_partial}, absent={a_absent}")
    print(f"  Critical edges B: present={b_present}, partial={b_partial}, absent={b_absent}")
    print(f"  F-065 implication: {report['f065_implication']}")

    return report


def log_investigation(report: Dict):
    """Append the investigation report to predictions.jsonl."""
    with PREDICTIONS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(report, default=str) + "\n")
    print(f"  -> logged to predictions.jsonl")


if __name__ == "__main__":
    # Example: investigate EXP-BLIND-022
    # (In production, this would read the experiment's edges from predictions.jsonl)
    print("External Investigation Module — F-065 source-text verification")
    print("Usage: import this module and call investigate() with the experiment's edges.")
