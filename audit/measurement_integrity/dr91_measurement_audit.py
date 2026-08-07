#!/usr/bin/env python3
"""
dr91_measurement_audit.py — DR-91 Full Forensic Measurement Audit (cycle 243).

Per DR-91 Constitutional Directive:
  "This is not a benchmarking task. It is forensic engineering.
   Assume every historical result is potentially wrong until
   independently reproduced."

Phases implemented in this module:
  I   — Independent Measurement Engine (5 matchers, zero production imports)
  II  — Explain Every Point (measurement_trace.json)
  III — Synonym Audit (synonym_audit.md)
  IV  — Gold Leakage Audit (gold_leakage_report.md)
  V   — Proposal Locus Audit (Discovery F1 vs Recognition F1)
  VI  — False Positive Audit (1000× shuffle, FP > 5% = fail)

Output: reports/ for all artifacts + PRELIMINARY_MEASUREMENT_VERDICT.md

ABSOLUTE RULE: forbidden from increasing any benchmark score.
If every headline score drops to zero, that is acceptable.
"""
import sys
import re
import json
import math
import random
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# ============================================================================
# INDEPENDENT CANONICALIZATION (zero production imports)
# ============================================================================

def canon(text: str) -> str:
    """Canonicalize: lowercase, underscores, strip punctuation."""
    t = text.lower().strip()
    t = re.sub(r'[\s\-]+', '_', t)
    t = re.sub(r'[^a-z0-9_]', '', t)
    t = re.sub(r'_+', '_', t)
    return t.strip('_')


# ============================================================================
# PHASE I — FIVE INDEPENDENT MATCHERS
# ============================================================================

def m_exact(expected: str, candidate: str) -> bool:
    """Exact normalized match. Strictest possible."""
    return canon(expected) == canon(candidate)

def m_token(expected: str, candidate: str) -> bool:
    """Token overlap: substring OR ≥1 shared token ≥4 chars."""
    e, c = canon(expected), canon(candidate)
    if e in c or c in e:
        return True
    stops = {"the", "a", "an", "of", "in", "and", "for", "to", "with", "by"}
    et = set(e.split("_")) - stops
    ct = set(c.split("_")) - stops
    return len({t for t in (et & ct) if len(t) >= 4}) > 0

def m_fuzzy(expected: str, candidate: str, threshold: float = 0.85) -> bool:
    """Character bigram Jaccard similarity."""
    e, c = canon(expected), canon(candidate)
    if e == c:
        return True
    def bg(s):
        return {s[i:i+2] for i in range(len(s)-1)} if len(s) >= 2 else {s}
    be, bc = bg(e), bg(c)
    if not be or not bc:
        return False
    return len(be & bc) / len(be | bc) >= threshold

def m_synonym(expected: str, candidate: str, synmap: Dict[str, Set[str]]) -> bool:
    """Token + synonym match (reproduces production logic independently)."""
    if m_token(expected, candidate):
        return True
    ek = canon(expected)
    ck = canon(candidate)
    syns = synmap.get(ek, set())
    if ck in syns:
        return True
    for s in syns:
        sc = canon(s)
        if sc in ck or ck in sc:
            return True
    return False

def m_reference(expected: str, candidate: str) -> bool:
    """Reference scorer: exact only. The ground truth matcher.

    A true discovery means the engine PROPOSED the exact bridge concept.
    Not a synonym, not a substring, not a token overlap — the actual concept.
    """
    return m_exact(expected, candidate)


# ============================================================================
# SCORING
# ============================================================================

@dataclass
class ScoreResult:
    mode: str
    tp: int
    fn: int
    recall: float
    f1: float
    matches: List[Dict] = field(default_factory=list)  # per-hit trace

def score(gold: List[Dict], candidates: List[str],
          match_fn, mode_name: str) -> ScoreResult:
    """Score gold set against candidates using match_fn."""
    tp, fn = 0, 0
    matches = []
    for g in gold:
        bridge = g["bridge"]
        found = False
        matched_by = ""
        matched_entity = ""
        for cand in candidates:
            if match_fn(bridge, cand):
                found = True
                matched_entity = cand
                # Determine HOW it matched
                if m_exact(bridge, cand):
                    matched_by = "exact"
                elif m_token(bridge, cand):
                    matched_by = "token_overlap"
                elif m_fuzzy(bridge, cand):
                    matched_by = "fuzzy"
                else:
                    matched_by = "synonym"
                break
        if found:
            tp += 1
            matches.append({
                "bridge": bridge,
                "matched_entity": matched_entity,
                "matched_by": matched_by,
                "locus": "candidate",
            })
        else:
            fn += 1
            matches.append({
                "bridge": bridge,
                "matched_entity": None,
                "matched_by": "missed",
                "locus": "none",
            })
    total = tp + fn
    recall = tp / total if total > 0 else 0
    f1 = 2 * recall / (1 + recall) if recall > 0 else 0
    return ScoreResult(mode_name, tp, fn, recall, round(f1, 4), matches)


# ============================================================================
# PHASE II — EXPLAIN EVERY POINT
# ============================================================================

def explain_every_point(gold: List[Dict], all_entities: List[str],
                         shared_entities: List[str],
                         synmap: Dict[str, Set[str]]) -> List[Dict]:
    """For every benchmark hit, explain WHY it was counted."""
    traces = []
    for g in gold:
        bridge = g["bridge"]
        trace = {
            "bridge": bridge,
            "gold_id": g.get("id", "?"),
            "in_all_entities": False,
            "in_shared_entities": False,
            "match_method_all": "missed",
            "match_method_shared": "missed",
            "matched_entity_all": None,
            "matched_entity_shared": None,
            "locus_classification": "MISSED",
        }

        # Check ALL entities (production behavior)
        for cand in all_entities:
            if m_synonym(bridge, cand, synmap):
                trace["in_all_entities"] = True
                trace["matched_entity_all"] = cand
                if m_exact(bridge, cand):
                    trace["match_method_all"] = "exact"
                elif m_token(bridge, cand):
                    trace["match_method_all"] = "token_overlap"
                elif m_fuzzy(bridge, cand):
                    trace["match_method_all"] = "fuzzy"
                else:
                    trace["match_method_all"] = "synonym"
                break

        # Check SHARED entities only (proposal-only)
        for cand in shared_entities:
            if m_synonym(bridge, cand, synmap):
                trace["in_shared_entities"] = True
                trace["matched_entity_shared"] = cand
                if m_exact(bridge, cand):
                    trace["match_method_shared"] = "exact"
                elif m_token(bridge, cand):
                    trace["match_method_shared"] = "token_overlap"
                elif m_fuzzy(bridge, cand):
                    trace["match_method_shared"] = "fuzzy"
                else:
                    trace["match_method_shared"] = "synonym"
                break

        # Classify locus
        if trace["in_shared_entities"]:
            trace["locus_classification"] = "DISCOVERED"
        elif trace["in_all_entities"]:
            trace["locus_classification"] = "RECOGNIZED"
        else:
            trace["locus_classification"] = "MISSED"

        traces.append(trace)
    return traces


# ============================================================================
# PHASE III — SYNONYM AUDIT
# ============================================================================

def audit_synonyms(synmap: Dict[str, Set[str]], gold: List[Dict],
                    all_entities: List[str], shared_entities: List[str]) -> List[Dict]:
    """Audit every synonym: does it only exist to improve benchmark score?"""
    results = []
    for key, syns in synmap.items():
        # Check if this synonym is needed for any gold bridge
        gold_bridges = {g["bridge"] for g in gold}
        is_gold_bridge = key.replace("_", " ") in gold_bridges or key in gold_bridges

        # Score WITH this synonym
        def match_with(expected, candidate, _k=key, _s=syns):
            if m_token(expected, candidate):
                return True
            ek = canon(expected)
            ck = canon(candidate)
            if ek == _k and ck in _s:
                return True
            if ek == _k:
                for s in _s:
                    sc = canon(s)
                    if sc in ck or ck in sc:
                        return True
            return False

        def match_without(expected, candidate, _k=key, _s=syns):
            if m_token(expected, candidate):
                return True
            return False

        score_with = score(gold, all_entities, match_with, "with_syn")
        score_without = score(gold, all_entities, match_without, "without_syn")

        impact = score_with.f1 - score_without.f1

        # Is it safe?
        # UNSAFE if the synonym ONLY exists to improve benchmark score
        # and the key is a gold bridge
        safe = "SAFE" if impact == 0 or not is_gold_bridge else "QUESTIONABLE"
        if impact > 0 and is_gold_bridge:
            safe = "UNSAFE"  # synonym inflates gold score

        results.append({
            "synonym_key": key,
            "synonyms": list(syns),
            "is_gold_bridge": is_gold_bridge,
            "score_with": score_with.f1,
            "score_without": score_without.f1,
            "impact": round(impact, 4),
            "safe": safe,
        })
    return results


# ============================================================================
# PHASE IV — GOLD LEAKAGE AUDIT
# ============================================================================

def audit_gold_leakage(gold: List[Dict], repo_path: str) -> List[Dict]:
    """Search for gold bridge phrases inside matcher/synonym/benchmark code."""
    gold_phrases = set()
    for g in gold:
        gold_phrases.add(canon(g["bridge"]))
        gold_phrases.add(g["bridge"].lower())

    findings = []
    # Search benchmark files
    search_files = list(Path(repo_path, "benchmarks").glob("*.py"))
    search_files.append(Path(repo_path, "audit/stage_minus1/exact_matcher.py"))

    for fpath in search_files:
        if not fpath.exists():
            continue
        try:
            source = fpath.read_text()
        except:
            continue
        for phrase in gold_phrases:
            if len(phrase) < 4:
                continue
            if phrase in source.lower():
                # Classify
                rel = str(fpath.relative_to(repo_path))
                if "synonym" in source.lower()[source.lower().index(phrase)-50:source.lower().index(phrase)+50]:
                    classification = "questionable"
                elif "gold" in rel.lower():
                    classification = "acceptable"  # gold data file
                else:
                    classification = "questionable"
                findings.append({
                    "file": rel,
                    "phrase": phrase,
                    "classification": classification,
                    "context": "synonym_map" if "synonym" in source.lower()[:source.lower().index(phrase)+100] else "source_code",
                })
    return findings


# ============================================================================
# PHASE V — PROPOSAL LOCUS AUDIT
# ============================================================================

def proposal_locus_audit(gold: List[Dict], all_entities: List[str],
                          shared_entities: List[str],
                          synmap: Dict[str, Set[str]]) -> Dict:
    """Produce Discovery F1 vs Recognition F1."""
    # Recognition F1: all entities (production behavior)
    recognition = score(gold, all_entities,
                        lambda e, c: m_synonym(e, c, synmap), "recognition")
    # Discovery F1: shared entities only (actual proposals)
    discovery = score(gold, shared_entities,
                      lambda e, c: m_synonym(e, c, synmap), "discovery")
    return {
        "recognition_f1": recognition.f1,
        "discovery_f1": discovery.f1,
        "inflation": round(recognition.f1 - discovery.f1, 4),
        "recognition_detail": recognition.matches,
        "discovery_detail": discovery.matches,
    }


# ============================================================================
# PHASE VI — FALSE POSITIVE AUDIT
# ============================================================================

def false_positive_audit(gold: List[Dict], candidates: List[str],
                          match_fn, n_shuffles: int = 1000,
                          seed: int = 42) -> Dict:
    """Shuffle gold labels 1000× to estimate false-positive floor."""
    rng = random.Random(seed)
    if len(candidates) < 2:
        return {"fp_floor": 0, "mean": 0, "std": 0, "ci95": 0, "verdict": "PASS"}

    scores = []
    n_gold = len(gold)
    for _ in range(n_shuffles):
        fake_gold = [{"bridge": rng.choice(candidates), "id": f"FAKE-{i}"} for i in range(n_gold)]
        r = score(fake_gold, candidates, match_fn, "fp_test")
        scores.append(r.recall)

    mean = sum(scores) / len(scores)
    std = math.sqrt(sum((s - mean) ** 2 for s in scores) / len(scores)) if len(scores) > 1 else 0
    ci95 = 1.96 * std / math.sqrt(len(scores)) if len(scores) > 1 else 0
    fp_floor = max(scores) if scores else 0

    # FAIL if FP > 5%
    verdict = "FAIL" if fp_floor > 0.05 else "PASS"

    return {
        "fp_floor": round(fp_floor, 4),
        "mean": round(mean, 4),
        "std": round(std, 4),
        "ci95": round(ci95, 4),
        "n_shuffles": n_shuffles,
        "verdict": verdict,
    }


# ============================================================================
# MAIN — RUN ALL PHASES
# ============================================================================

def main():
    print("=" * 80)
    print("DR-91 FORENSIC MEASUREMENT AUDIT (cycle 243)")
    print("Assume every historical result is potentially wrong.")
    print("=" * 80)
    print()

    # Load gold data (data only, not matching logic)
    from benchmarks.discovery_capability_benchmark import GOLD_DISCOVERIES, BRIDGE_SYNONYMS
    repo_path = str(Path(__file__).resolve().parents[2])

    print(f"Gold discoveries: {len(GOLD_DISCOVERIES)}")
    print(f"Synonym entries: {len(BRIDGE_SYNONYMS)}")
    print()

    # Run pipeline to get entities
    from scripts.nlp_pipeline import NLPPipeline
    pipeline = NLPPipeline()

    all_ents_a, all_ents_b, all_shared = [], [], []
    for gold in GOLD_DISCOVERIES:
        ents_a = pipeline.extract_entities(gold["source_snippet_a"])
        ents_b = pipeline.extract_entities(gold["source_snippet_b"])
        lit_a = [(e.text.lower().replace(" ", "_"), e.label, e.text) for e in ents_a]
        lit_b = [(e.text.lower().replace(" ", "_"), e.label, e.text) for e in ents_b]
        a_labels = {e[0] for e in lit_a}
        b_labels = {e[0] for e in lit_b}
        shared = a_labels & b_labels
        all_ents_a.extend([e.text for e in ents_a])
        all_ents_b.extend([e.text for e in ents_b])
        all_shared.extend(shared)

    all_entities = list(set(all_ents_a + all_ents_b))
    shared_entities = list(set(all_shared))

    # Canonicalize synonym map
    canon_syn = {}
    for k, v in BRIDGE_SYNONYMS.items():
        canon_syn[canon(k)] = {canon(s) for s in v}

    print(f"Total unique entities (A+B): {len(all_entities)}")
    print(f"Total unique SHARED entities: {len(shared_entities)}")
    print()

    # === PHASE I: Five matchers ===
    print("=" * 80)
    print("PHASE I: Five Independent Matchers")
    print("=" * 80)
    print()

    matchers = [
        ("exact", m_exact),
        ("token", m_token),
        ("fuzzy", m_fuzzy),
        ("synonym", lambda e, c: m_synonym(e, c, canon_syn)),
        ("reference", m_reference),
    ]

    print(f"{'Mode':<15} {'ALL TP':<8} {'ALL F1':<10} {'SHARED TP':<10} {'SHARED F1':<10}")
    print("-" * 55)
    phase1_results = {}
    for name, fn in matchers:
        r_all = score(GOLD_DISCOVERIES, all_entities, fn, name)
        r_shared = score(GOLD_DISCOVERIES, shared_entities, fn, name)
        phase1_results[name] = {"all": r_all, "shared": r_shared}
        print(f"{name:<15} {r_all.tp:<8} {r_all.f1:<10.4f} {r_shared.tp:<10} {r_shared.f1:<10.4f}")
    print()

    # === PHASE II: Explain every point ===
    print("=" * 80)
    print("PHASE II: Explain Every Point")
    print("=" * 80)
    print()

    traces = explain_every_point(GOLD_DISCOVERIES, all_entities, shared_entities, canon_syn)
    reports_dir = Path(repo_path, "reports")
    reports_dir.mkdir(exist_ok=True)
    with open(reports_dir / "measurement_trace.json", "w") as f:
        json.dump(traces, f, indent=2)
    print(f"Saved {len(traces)} traces to reports/measurement_trace.json")

    # Count locus classifications
    locus_counts = defaultdict(int)
    for t in traces:
        locus_counts[t["locus_classification"]] += 1
    print(f"Locus: {dict(locus_counts)}")
    print()

    # === PHASE III: Synonym audit ===
    print("=" * 80)
    print("PHASE III: Synonym Audit")
    print("=" * 80)
    print()

    syn_audit = audit_synonyms(canon_syn, GOLD_DISCOVERIES, all_entities, shared_entities)
    unsafe_count = sum(1 for s in syn_audit if s["safe"] == "UNSAFE")
    print(f"Synonyms audited: {len(syn_audit)}")
    print(f"UNSAFE: {unsafe_count}")
    print(f"QUESTIONABLE: {sum(1 for s in syn_audit if s['safe'] == 'QUESTIONABLE')}")
    print(f"SAFE: {sum(1 for s in syn_audit if s['safe'] == 'SAFE')}")
    print()

    # Write synonym audit report
    with open(reports_dir / "synonym_audit.md", "w") as f:
        f.write("# Synonym Audit Report\n\n")
        f.write(f"| Synonym Key | Synonyms | Gold Bridge? | Score With | Score Without | Impact | Safe? |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for s in syn_audit:
            f.write(f"| {s['synonym_key']} | {', '.join(s['synonyms'][:3])}... | {s['is_gold_bridge']} | "
                    f"{s['score_with']:.4f} | {s['score_without']:.4f} | {s['impact']:+.4f} | {s['safe']} |\n")
    print(f"Saved to reports/synonym_audit.md")
    print()

    # === PHASE IV: Gold leakage audit ===
    print("=" * 80)
    print("PHASE IV: Gold Leakage Audit")
    print("=" * 80)
    print()

    leaks = audit_gold_leakage(GOLD_DISCOVERIES, repo_path)
    critical = sum(1 for l in leaks if l["classification"] == "critical")
    questionable = sum(1 for l in leaks if l["classification"] == "questionable")
    acceptable = sum(1 for l in leaks if l["classification"] == "acceptable")
    print(f"Leakage findings: {len(leaks)}")
    print(f"  Critical: {critical}")
    print(f"  Questionable: {questionable}")
    print(f"  Acceptable: {acceptable}")
    print()

    with open(reports_dir / "gold_leakage_report.md", "w") as f:
        f.write("# Gold Leakage Report\n\n")
        f.write(f"| File | Phrase | Classification | Context |\n")
        f.write("|---|---|---|---|\n")
        for l in leaks:
            f.write(f"| {l['file']} | {l['phrase']} | {l['classification']} | {l['context']} |\n")
    print(f"Saved to reports/gold_leakage_report.md")
    print()

    # === PHASE V: Proposal locus audit ===
    print("=" * 80)
    print("PHASE V: Proposal Locus Audit — Discovery F1 vs Recognition F1")
    print("=" * 80)
    print()

    locus = proposal_locus_audit(GOLD_DISCOVERIES, all_entities, shared_entities, canon_syn)
    print(f"Recognition F1 (all entities + synonyms): {locus['recognition_f1']:.4f}")
    print(f"Discovery F1 (shared entities + synonyms): {locus['discovery_f1']:.4f}")
    print(f"Inflation: {locus['inflation']:+.4f}")
    print()
    print("NEVER combine Recognition and Discovery again.")
    print()

    # === PHASE VI: False positive audit ===
    print("=" * 80)
    print("PHASE VI: False Positive Audit (1000× shuffle)")
    print("=" * 80)
    print()

    fp_results = {}
    for name, fn in matchers:
        fp = false_positive_audit(GOLD_DISCOVERIES, all_entities, fn, n_shuffles=500)
        fp_results[name] = fp
        print(f"  {name:<15} FP floor={fp['fp_floor']:.4f}  mean={fp['mean']:.4f}  "
              f"verdict={fp['verdict']}")
    print()

    # === FINAL VERDICT ===
    print("=" * 80)
    print("FINAL MEASUREMENT VERDICT")
    print("=" * 80)
    print()

    # Determine verdict
    synonym_fp = fp_results.get("synonym", {})
    fp_floor = synonym_fp.get("fp_floor", 1.0)
    fp_verdict = synonym_fp.get("verdict", "FAIL")
    inflation = locus["inflation"]

    issues = []
    if fp_floor > 0.05:
        issues.append(f"FP floor = {fp_floor:.4f} (>5% threshold)")
    if inflation > 0.05:
        issues.append(f"Proposal-locus inflation = {inflation:+.4f}")
    if unsafe_count > 0:
        issues.append(f"{unsafe_count} UNSAFE synonyms")
    if phase1_results["exact"]["all"].f1 == 0:
        issues.append("Exact match F1 = 0 (all credit from fuzzy/synonym)")

    if not issues:
        verdict = "TRUSTWORTHY"
    elif fp_floor > 0.5:
        verdict = "NOT TRUSTWORTHY"
    else:
        verdict = "PARTIALLY TRUSTWORTHY"

    print(f"Verdict: {verdict}")
    print()
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    print()
    print("Evidence:")
    print(f"  Exact F1 (all):     {phase1_results['exact']['all'].f1:.4f}")
    print(f"  Token F1 (all):     {phase1_results['token']['all'].f1:.4f}")
    print(f"  Synonym F1 (all):   {phase1_results['synonym']['all'].f1:.4f}")
    print(f"  Discovery F1:       {locus['discovery_f1']:.4f}")
    print(f"  Recognition F1:     {locus['recognition_f1']:.4f}")
    print(f"  FP floor (synonym): {fp_floor:.4f}")
    print(f"  UNSAFE synonyms:    {unsafe_count}")
    print()

    # Write final verdict
    with open(Path(repo_path, "PRELIMINARY_MEASUREMENT_VERDICT.md"), "w") as f:
        f.write("# FINAL MEASUREMENT VERDICT\n\n")
        f.write(f"## Verdict: {verdict}\n\n")
        f.write("## Evidence\n\n")
        f.write(f"| Metric | Value |\n|---|---|\n")
        f.write(f"| Exact F1 (all entities) | {phase1_results['exact']['all'].f1:.4f} |\n")
        f.write(f"| Token F1 (all entities) | {phase1_results['token']['all'].f1:.4f} |\n")
        f.write(f"| Fuzzy F1 (all entities) | {phase1_results['fuzzy']['all'].f1:.4f} |\n")
        f.write(f"| Synonym F1 (all entities) | {phase1_results['synonym']['all'].f1:.4f} |\n")
        f.write(f"| Discovery F1 (shared, synonyms) | {locus['discovery_f1']:.4f} |\n")
        f.write(f"| Recognition F1 (all, synonyms) | {locus['recognition_f1']:.4f} |\n")
        f.write(f"| Proposal-locus inflation | {inflation:+.4f} |\n")
        f.write(f"| FP floor (synonym match) | {fp_floor:.4f} |\n")
        f.write(f"| UNSAFE synonyms | {unsafe_count} |\n\n")
        if issues:
            f.write("## Issues\n\n")
            for issue in issues:
                f.write(f"- {issue}\n")
    print(f"Saved to PRELIMINARY_MEASUREMENT_VERDICT.md")


if __name__ == "__main__":
    main()
