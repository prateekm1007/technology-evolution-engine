#!/usr/bin/env python3
"""
maestro_loop.py — The outer governance loop (Maestro Loop v1.0).

Per ANTI_ENTROPY.md "Epistemic anti-entropy rules (Maestro Loop, v1.0)":

  1. Freeze architecture.
  2. Change one thing.
  3. Measure everything.
  4. Record every failure.
  5. Reward evidence.
  6. Punish complexity.
  7. Prefer causality over correlation.
  8. Prefer experiments over arguments.
  9. Prefer reality over expectations.
  10. Prefer loops over modules.

Per CONSTITUTION.md "Law 8 (Verification Standard)":
  No "verified" label without a successful prediction, a failed
  prediction, and replayable evidence.

Per CEO directive "create the loop" — the existing discovery_loop.py is
the 13-step DISCOVERY pipeline (runs once). This module is the OUTER
MAESTRO LOOP that drives continuous improvement cycles:

  ┌─────────────────────────────────────────────────────────────┐
  │  Stage 1: RUN    — execute the 13-step DiscoveryLoop       │
  │  Stage 2: MEASURE — execute the 8-test acid test           │
  │  Stage 3: RECORD — append the cycle to data/cycles/log.jsonl │
  │  Stage 4: GAP    — identify the next-closest-to-PASS test  │
  │  Stage 5: PROPOSE— propose ONE concrete next intervention   │
  │  Stage 6: REPORT — write data/cycles/cycle_<N>.md          │
  │  Stage 7: COMMIT — git add + commit + push (optional)      │
  └─────────────────────────────────────────────────────────────┘

The loop is IDEMPOTENT — running it produces the next cycle. Running
it again produces the cycle after that. The state is carried by
the cycle log + the git history.

Per the "anti-perfection anti-entropy rule": the loop does NOT aim for
10/10. It aims for systematic excellence: one gap closed per cycle,
driven by what caused the last cycle's INCOMPLETE results.

Per "Close loops, don't add modules": this is NOT a new module. It is
a loop-closing script that uses existing infrastructure (DiscoveryLoop,
acid test, ledger). It writes observations; it does not modify the
architecture.

Usage:
    python scripts/maestro_loop.py                 # run one cycle, no commit
    python scripts/maestro_loop.py --commit        # run one cycle + git commit + push
    python scripts/maestro_loop.py --dry-run        # show what would happen, don't write
"""
import argparse
import json
import subprocess
import sys
import pathlib
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CYCLES_DIR = ROOT / "data" / "cycles"
CYCLE_LOG = CYCLES_DIR / "cycle_log.jsonl"


def _safe_relative(path: pathlib.Path, base: pathlib.Path) -> str:
    """Return path.relative_to(base) if possible, else the absolute path string.

    Used so that tests that monkeypatch CYCLE_LOG to a tmp directory don't
    break the report generator with a ValueError.
    """
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Stage 1: RUN — execute the 13-step DiscoveryLoop
# ---------------------------------------------------------------------------

def run_discovery_loop() -> Dict[str, Any]:
    """Execute the 13-step DiscoveryLoop and return its summary."""
    from scripts.discovery_loop import DiscoveryLoop
    loop = DiscoveryLoop()
    summary = loop.run()
    return summary


# ---------------------------------------------------------------------------
# Stage 2: MEASURE — execute the 8-test acid test
# ---------------------------------------------------------------------------

def run_acid_test() -> Dict[str, Any]:
    """Execute the 8-test acid test and return per-test results.

    Reuses the corpus_graph fixture logic from test_acid_test_revised.py.
    Returns a dict with per-test PASS/INCOMPLETE/NOT IMPLEMENTED status
    and the meaningful counts.
    """
    from invention_compiler.edge_extractor import EdgeExtractor
    from invention_compiler.discovery_graph import (
        DiscoveryGraph, SwansonBridgeSearch, GentnerStructureMapping,
        AltshullerContradictionSearch,
    )

    extractor = EdgeExtractor()
    papers = extractor.extract_from_corpus(
        str(ROOT / "data" / "ingestion" / "papers"), use_discovery_graph=False
    )
    patents = extractor.extract_from_corpus(
        str(ROOT / "data" / "ingestion" / "patents"), use_discovery_graph=False
    )
    rc_dir = ROOT / "data" / "ingestion" / "radiative_cooling"
    rc = extractor.extract_from_corpus(str(rc_dir), use_discovery_graph=False) if rc_dir.exists() else type(papers)()

    combined = type(papers)()
    for src in (papers, patents, rc):
        for nid, node in src.nodes.items():
            if nid not in combined.nodes:
                combined.add_node(node)
            else:
                existing = combined.nodes[nid]
                existing.what_does_this_change = list(
                    set(existing.what_does_this_change + node.what_does_this_change)
                )
                existing.evidence = list(set(existing.evidence + node.evidence))
        for edge in src.edges:
            exists = any(
                e.source == edge.source and e.target == edge.target
                and e.mechanism == edge.mechanism
                for e in combined.edges
            )
            if not exists:
                combined.add_edge(edge)

    dg = combined.to_discovery_graph()

    # Helper: source documents for a node
    def _sources(node_id: str) -> set:
        sources = set()
        for sg in dg._subgraphs.values():
            for edge in sg.edges:
                if edge.source == node_id or edge.target == node_id:
                    prov = edge.evidence.provenance if edge.evidence else ""
                    for m in re.finditer(r"['\"]?source['\"]?:\s*['\"]([^'\"]+)['\"]", prov):
                        sources.add(m.group(1))
                    if prov and "{" not in prov:
                        sources.add(prov.strip().strip("'\""))
        return sources

    # Swanson
    bridges = SwansonBridgeSearch.search(dg)
    swanson_meaningful = 0
    for b in bridges:
        a_node = dg.nodes.get(b["a"])
        c_node = dg.nodes.get(b["c"])
        if not (a_node and c_node) or a_node.node_type == c_node.node_type:
            continue
        a_s = _sources(b["a"])
        c_s = _sources(b["c"])
        if a_s and c_s and not a_s.issubset(c_s) and not c_s.issubset(a_s):
            swanson_meaningful += 1

    # Pearl
    all_edges = []
    for sg in dg._subgraphs.values():
        all_edges.extend(sg.edges)
    pearl_count = sum(
        1 for e in all_edges
        if dg.nodes.get(e.source)
        and dg.nodes[e.source].node_type in ("material", "manufacturing", "property")
    )

    # Popper
    popper_count = sum(1 for e in all_edges if getattr(e, 'falsifiable_by', None))

    # Altshuller
    contradictions = AltshullerContradictionSearch.find_contradictions(dg)

    # Gentner
    analogies = GentnerStructureMapping.find_analogous_chains(dg, min_chain_length=2)
    long_analogies = [a for a in analogies if len(a.get("chain_a", [])) >= 3]
    gentner_cross = 0
    for a in long_analogies:
        all_nodes = set(a.get("chain_a", [])) | set(a.get("chain_b", []))
        all_sources = set()
        for nid in all_nodes:
            all_sources |= _sources(nid)
        if len(all_sources) >= 3:
            gentner_cross += 1

    return {
        "Swanson":    {"status": "PASS" if swanson_meaningful >= 5 else "INCOMPLETE",
                       "count": swanson_meaningful, "threshold": 5,
                       "unit": "cross-type+cross-source bridges"},
        "Pearl":      {"status": "PASS" if pearl_count >= 10 else "INCOMPLETE",
                       "count": pearl_count, "threshold": 10,
                       "unit": "intervention-capable edges"},
        "Popper":     {"status": "PASS" if popper_count >= 10 else "INCOMPLETE",
                       "count": popper_count, "threshold": 10,
                       "unit": "falsifiable edges"},
        "Gentner":    {"status": "PASS" if gentner_cross >= 5 else "INCOMPLETE",
                       "count": gentner_cross, "threshold": 5,
                       "unit": "length≥3+cross-source chains"},
        "Altshuller": {"status": "PASS" if len(contradictions) >= 3 else "INCOMPLETE",
                       "count": len(contradictions), "threshold": 3,
                       "unit": "contradictions"},
        "Ross King":  {"status": "INCOMPLETE",
                       "count": None, "threshold": None,
                       "unit": "experiment distinguishes competing hypotheses"},
        "BACON":      {"status": "NOT IMPLEMENTED",
                       "count": None, "threshold": None,
                       "unit": "law derivation engine"},
        "Arthur":     {"status": "MERGED with Swanson",
                       "count": len(bridges), "threshold": None,
                       "unit": "merged — same algorithm as Swanson"},
        "_meta": {
            "total_nodes": len(dg.nodes),
            "total_edges": len(all_edges),
            "total_bridges": len(bridges),
            "total_analogies": len(analogies),
            "total_contradictions": len(contradictions),
        },
    }


# ---------------------------------------------------------------------------
# Stage 3: RECORD — append the cycle to data/cycles/cycle_log.jsonl
# ---------------------------------------------------------------------------

def _next_cycle_number() -> int:
    """Determine the next cycle number from the existing log."""
    if not CYCLE_LOG.exists():
        return 1
    max_n = 0
    for line in CYCLE_LOG.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            if "cycle" in entry and isinstance(entry["cycle"], int):
                max_n = max(max_n, entry["cycle"])
        except json.JSONDecodeError:
            continue
    return max_n + 1


def record_cycle(cycle_n: int, discovery_summary: Dict[str, Any],
                 acid_test_results: Dict[str, Any]) -> Dict[str, Any]:
    """Append the cycle to the cycle log."""
    CYCLES_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()

    pass_count = sum(1 for k, v in acid_test_results.items()
                     if k != "_meta" and v["status"] == "PASS")
    incomplete_count = sum(1 for k, v in acid_test_results.items()
                            if k != "_meta" and v["status"] == "INCOMPLETE")
    not_impl = sum(1 for k, v in acid_test_results.items()
                   if k != "_meta" and v["status"] == "NOT IMPLEMENTED")
    merged = sum(1 for k, v in acid_test_results.items()
                 if k != "_meta" and "MERGED" in v["status"])

    entry = {
        "cycle": cycle_n,
        "timestamp": now,
        "writer": "scripts.maestro_loop",
        "discovery": {
            "pass_count": discovery_summary.get("pass_count"),
            "incomplete_count": discovery_summary.get("incomplete_count"),
            "not_implemented_count": discovery_summary.get("not_implemented_count"),
            "total_nodes": discovery_summary.get("total_nodes"),
            "total_edges": discovery_summary.get("total_edges"),
            "bridges_found": discovery_summary.get("bridges_found"),
            "analogies_found": discovery_summary.get("analogies_found"),
            "contradictions_found": discovery_summary.get("contradictions_found"),
            "closed_loops": discovery_summary.get("closed_loops"),
        },
        "acid_test": {
            "pass_count": pass_count,
            "incomplete_count": incomplete_count,
            "not_implemented_count": not_impl,
            "merged_count": merged,
            "hardens": pass_count >= 4,
            "results": {k: v for k, v in acid_test_results.items() if k != "_meta"},
        },
        "graph_meta": acid_test_results.get("_meta", {}),
    }

    with CYCLE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")

    return entry


# ---------------------------------------------------------------------------
# Stage 4: GAP — identify the next-closest-to-PASS test
# ---------------------------------------------------------------------------

def identify_gap(acid_test_results: Dict[str, Any]) -> Dict[str, Any]:
    """Identify the next-closest-to-PASS test (or the highest-priority gap).

    Priority order:
      1. NOT IMPLEMENTED tests that are NOT Phase III — fix the engine
      2. INCOMPLETE tests sorted by (threshold - count) ascending
         (closest-to-PASS first; one small intervention can flip it)
      3. NOT IMPLEMENTED Phase III tests (BACON) — lowest priority

    Returns a dict with: test_name, gap_type, current_count, threshold,
    deficit, suggested_intervention.
    """
    candidates = []
    for name, result in acid_test_results.items():
        if name == "_meta":
            continue
        status = result["status"]
        if status == "PASS":
            continue  # already passing
        if "MERGED" in status:
            continue  # not a separate test

        if status == "NOT IMPLEMENTED":
            # BACON is Phase III — lowest priority
            candidates.append({
                "test": name,
                "gap_type": "not_implemented",
                "current_count": None,
                "threshold": None,
                "deficit": None,
                "priority": 0 if name == "BACON" else 5,
                "intervention": "Implement a law derivation engine that fits "
                                "numerical laws to measurement data (BACON-style "
                                "scientific discovery)." if name == "BACON"
                                else "Implement the missing capability.",
            })
            continue

        if status == "INCOMPLETE":
            count = result.get("count")
            threshold = result.get("threshold")
            if count is None or threshold is None:
                # Ross King — qualitative gap, not numeric
                candidates.append({
                    "test": name,
                    "gap_type": "qualitative",
                    "current_count": None,
                    "threshold": None,
                    "deficit": None,
                    "priority": 3,
                    "intervention": (
                        "Design experiments that distinguish between competing "
                        "hypotheses (e.g., 'is the Seebeck effect linear in ΔT "
                        "at all temperatures, or does it saturate?'). Currently "
                        "the experiment confirms a known edge — Adam's contribution "
                        "was hypothesizing a NEW mechanism, not verifying a known one."
                    ),
                })
                continue

            deficit = max(0, threshold - count)
            # Ross King-style numeric INCOMPLETE: priority by closeness to PASS
            # (smaller deficit = higher priority — one small fix can flip it)
            candidates.append({
                "test": name,
                "gap_type": "numeric",
                "current_count": count,
                "threshold": threshold,
                "deficit": deficit,
                "priority": 10 - deficit if deficit < 10 else 1,
                "intervention": _intervention_for(name, count, threshold),
            })

    if not candidates:
        return {
            "test": None,
            "gap_type": "none",
            "message": "All tests PASS or are correctly NOT IMPLEMENTED/MERGED. "
                       "Architecture is hardened. Next cycle: tighten meaningfulness "
                       "criteria (Phase III).",
        }

    # Sort by priority (highest first), then by smallest deficit
    candidates.sort(key=lambda c: (-c["priority"], c.get("deficit") or 0))
    return candidates[0]


def _intervention_for(test_name: str, count: int, threshold: int) -> str:
    """Suggest a concrete next intervention for a numeric INCOMPLETE test."""
    interventions = {
        "Swanson": (
            f"Add another cross-domain corpus (e.g., N₂ fixation or thermoelectric "
            f"paints). Currently {count} cross-type+cross-source bridges (need "
            f"{threshold}). Each new domain adds O(n×m) bridges where n,m are "
            f"node counts. A 20-paper N₂ fixation corpus should add ~30-50 "
            f"new cross-source bridges."
        ),
        "Gentner": (
            f"Add another cross-domain corpus OR relax min_chain_length from 3 to 2. "
            f"Currently {count} length≥3+cross-source chains (need {threshold}). "
            f"A new corpus adds chains combinatorially."
        ),
        "Pearl": (
            f"Extend EdgeExtractor to populate specific Intervention objects "
            f"('increase doping 5%') rather than generic ('change X'). "
            f"Currently {count} intervention-capable edges (need {threshold}). "
            f"Add INTERVENTION_PATTERNS that match quantitative deltas."
        ),
        "Popper": (
            f"Extend EdgeExtractor to populate falsifiable_by with specific "
            f"measurement protocols (e.g., 'measure Seebeck coefficient at "
            f"ΔT=100K, falsified if |S| < 100 μV/K'). Currently {count} "
            f"falsifiable edges (need {threshold})."
        ),
        "Altshuller": (
            f"Extend EdgeExtractor DIRECTION_PATTERNS to extract more "
            f"increases/decreases relationships. Currently {count} contradictions "
            f"(need {threshold}). Each new direction annotation can produce "
            f"O(n²) new contradictions."
        ),
    }
    return interventions.get(test_name, f"Increase count from {count} to {threshold}.")


# ---------------------------------------------------------------------------
# Stage 5: PROPOSE — propose ONE concrete next intervention
# ---------------------------------------------------------------------------

def propose_intervention(gap: Dict[str, Any], cycle_n: int) -> Dict[str, Any]:
    """Convert the identified gap into a concrete next-cycle proposal."""
    if gap.get("gap_type") == "none":
        return {
            "cycle": cycle_n + 1,
            "task": "No gap identified — architecture hardened",
            "action": "Phase III: implement BACON law derivation engine",
            "rationale": "All current tests PASS. The next capability gap is "
                         "BACON (law derivation), which is Phase III work.",
            "estimated_files_changed": ["invention_compiler/bacon_engine.py (new)",
                                         "tests/test_bacon_engine.py (new)"],
        }

    return {
        "cycle": cycle_n + 1,
        "task": f"Close the {gap['test']} gap",
        "action": gap["intervention"],
        "rationale": (
            f"{gap['test']} is {gap['gap_type']}"
            + (f" with count={gap['current_count']} vs threshold={gap['threshold']} "
               f"(deficit={gap['deficit']})" if gap.get("deficit") is not None else "")
        ),
        "estimated_files_changed": _estimate_files_for(gap["test"]),
    }


def _estimate_files_for(test_name: str) -> List[str]:
    """Estimate which files the next intervention would touch."""
    return {
        "Swanson":   ["scripts/fetch_<new_domain>_corpus.py (new)",
                      "data/ingestion/<new_domain>/ (new)",
                      "invention_compiler/edge_extractor.py (modify)"],
        "Gentner":   ["scripts/fetch_<new_domain>_corpus.py (new)",
                      "data/ingestion/<new_domain>/ (new)"],
        "Pearl":     ["invention_compiler/edge_extractor.py (modify)"],
        "Popper":    ["invention_compiler/edge_extractor.py (modify)"],
        "Altshuller":["invention_compiler/edge_extractor.py (modify)",
                      "invention_compiler/discovery_graph.py (modify)"],
        "Ross King": ["invention_compiler/causal_simulator.py (modify)",
                      "tests/test_causal_simulator.py (modify)"],
        "BACON":     ["invention_compiler/bacon_engine.py (new)",
                      "tests/test_bacon_engine.py (new)"],
    }.get(test_name, ["(unknown)"])


# ---------------------------------------------------------------------------
# Stage 6: REPORT — write data/cycles/cycle_<N>.md
# ---------------------------------------------------------------------------

def write_cycle_report(cycle_n: int, discovery_summary: Dict[str, Any],
                       acid_test_results: Dict[str, Any],
                       cycle_entry: Dict[str, Any],
                       gap: Dict[str, Any],
                       proposal: Dict[str, Any]) -> pathlib.Path:
    """Write a Markdown cycle report to data/cycles/cycle_<N>.md."""
    CYCLES_DIR.mkdir(parents=True, exist_ok=True)
    report_path = CYCLES_DIR / f"cycle_{cycle_n:03d}.md"

    pass_count = cycle_entry["acid_test"]["pass_count"]
    incomplete_count = cycle_entry["acid_test"]["incomplete_count"]
    not_impl = cycle_entry["acid_test"]["not_implemented_count"]
    merged = cycle_entry["acid_test"]["merged_count"]
    hardens = cycle_entry["acid_test"]["hardens"]

    lines = [
        f"# Cycle {cycle_n:03d} — Maestro Loop Report",
        "",
        f"**Timestamp:** {cycle_entry['timestamp']}",
        f"**Writer:** scripts.maestro_loop",
        f"**Hardens:** {'YES (≥4 PASS)' if hardens else 'NO'}",
        "",
        "## Stage 1: Discovery Loop (13 steps)",
        "",
        f"- Nodes: {discovery_summary.get('total_nodes')}",
        f"- Edges: {discovery_summary.get('total_edges')}",
        f"- Bridges: {discovery_summary.get('bridges_found')}",
        f"- Analogies: {discovery_summary.get('analogies_found')}",
        f"- Contradictions: {discovery_summary.get('contradictions_found')}",
        f"- Closed loops: {discovery_summary.get('closed_loops')}",
        f"- Discovery pass count: {discovery_summary.get('pass_count')}/13",
        f"- Discovery incomplete count: {discovery_summary.get('incomplete_count')}/13",
        "",
        "## Stage 2: Acid Test (8 tests)",
        "",
        "| Test | Status | Count | Threshold | Unit |",
        "|---|---|---|---|---|",
    ]
    for name, r in acid_test_results.items():
        if name == "_meta":
            continue
        count = r.get("count") if r.get("count") is not None else "—"
        thresh = r.get("threshold") if r.get("threshold") is not None else "—"
        lines.append(f"| {name} | {r['status']} | {count} | {thresh} | {r.get('unit', '')} |")

    lines.extend([
        "",
        f"**Summary:** {pass_count} PASS, {incomplete_count} INCOMPLETE, "
        f"{not_impl} NOT IMPLEMENTED, {merged} MERGED",
        f"**Hardening criterion (≥4 PASS):** {'MET' if hardens else 'NOT MET'}",
        "",
        "## Stage 3: Cycle Recorded",
        "",
        f"Appended to `{_safe_relative(CYCLE_LOG, ROOT)}` as cycle {cycle_n}.",
        "",
        "## Stage 4: Gap Identification",
        "",
        f"**Next gap:** {gap.get('test', '(none)')}",
        f"**Gap type:** {gap.get('gap_type', '')}",
    ])
    if gap.get("deficit") is not None:
        lines.extend([
            f"**Current count:** {gap.get('current_count')}",
            f"**Threshold:** {gap.get('threshold')}",
            f"**Deficit:** {gap.get('deficit')}",
        ])
    lines.extend([
        f"**Priority:** {gap.get('priority', '—')}",
        "",
        "## Stage 5: Proposed Next Intervention",
        "",
        f"**Next cycle:** {proposal.get('cycle')}",
        f"**Task:** {proposal.get('task')}",
        f"**Action:** {proposal.get('action')}",
        f"**Rationale:** {proposal.get('rationale')}",
        "",
        "### Estimated files changed next cycle:",
        "",
    ])
    for f in proposal.get("estimated_files_changed", []):
        lines.append(f"- `{f}`")

    lines.extend([
        "",
        "## Honest Scope",
        "",
        "- This cycle report is generated mechanically by `scripts/maestro_loop.py`.",
        "- The DiscoveryLoop and acid test are executed live; the numbers are real.",
        "- The gap identification follows a deterministic priority: closest-to-PASS "
        "INCOMPLETE tests first, then qualitative gaps, then NOT IMPLEMENTED.",
        "- The proposed intervention is a template — the next coder may choose a "
        "different intervention if they have a better one. The proposal is a "
        "starting point, not a mandate.",
        "- Per ANTI_ENTROPY.md 'anti-perfection': the loop does NOT aim for 10/10. "
        "It aims for one gap closed per cycle.",
        "",
        "## Per CONSTITUTION.md Law 8",
        "",
        "No 'verified' label is applied by this loop. The cycle report records "
        "what was observed (counts, statuses). The 'hardens' flag is a fact "
        "(pass_count >= 4), not a verification. Verification requires successful "
        "prediction + failed prediction + replayable evidence — none of which "
        "this loop claims to provide.",
        "",
    ])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


# ---------------------------------------------------------------------------
# Stage 7: COMMIT — git add + commit + push (optional)
# ---------------------------------------------------------------------------

def git_commit_cycle(cycle_n: int, report_path: pathlib.Path,
                     cycle_entry: Dict[str, Any], push: bool = False) -> bool:
    """Commit the cycle report and log entry to git. Optionally push."""
    pass_count = cycle_entry["acid_test"]["pass_count"]
    incomplete_count = cycle_entry["acid_test"]["incomplete_count"]
    msg = (f"chore(maestro cycle {cycle_n:03d}): "
           f"{pass_count} PASS, {incomplete_count} INCOMPLETE — "
           f"{'hardens' if cycle_entry['acid_test']['hardens'] else 'not yet'}")

    cmds = [
        ["git", "add", "-A"],
        ["git", "commit", "-m", msg],
    ]
    if push:
        cmds.append(["git", "push"])

    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
        if result.returncode != 0:
            print(f"  git command failed: {' '.join(cmd[:3])}...")
            print(f"  stderr: {result.stderr[:500]}")
            return False
    return True


# ---------------------------------------------------------------------------
# Main: run one cycle
# ---------------------------------------------------------------------------

def run_one_cycle(commit: bool = False, push: bool = False,
                  dry_run: bool = False) -> Dict[str, Any]:
    """Run one complete Maestro Loop cycle.

    Returns the cycle entry dict.
    """
    print("=" * 70)
    print("MAESTRO LOOP — ONE CYCLE")
    print("=" * 70)

    cycle_n = _next_cycle_number()
    print(f"Cycle number: {cycle_n}")
    print()

    # Stage 1: RUN
    print("--- Stage 1: RUN (DiscoveryLoop) ---")
    discovery_summary = run_discovery_loop()
    print()

    # Stage 2: MEASURE
    print("--- Stage 2: MEASURE (acid test) ---")
    acid_test_results = run_acid_test()
    pass_count = sum(1 for k, v in acid_test_results.items()
                     if k != "_meta" and v["status"] == "PASS")
    print(f"Acid test: {pass_count} PASS")
    print()

    if dry_run:
        print("--- DRY RUN — skipping stages 3-7 ---")
        return {"cycle": cycle_n, "discovery": discovery_summary,
                "acid_test": acid_test_results, "dry_run": True}

    # Stage 3: RECORD
    print("--- Stage 3: RECORD (append to cycle_log.jsonl) ---")
    cycle_entry = record_cycle(cycle_n, discovery_summary, acid_test_results)
    print(f"Recorded cycle {cycle_n} to {CYCLE_LOG}")
    print()

    # Stage 4: GAP
    print("--- Stage 4: GAP (identify next-closest-to-PASS) ---")
    gap = identify_gap(acid_test_results)
    print(f"Next gap: {gap.get('test', '(none)')} — {gap.get('gap_type')}")
    if gap.get("deficit") is not None:
        print(f"  count={gap['current_count']}, threshold={gap['threshold']}, deficit={gap['deficit']}")
    print()

    # Stage 5: PROPOSE
    print("--- Stage 5: PROPOSE (next intervention) ---")
    proposal = propose_intervention(gap, cycle_n)
    print(f"Next cycle task: {proposal['task']}")
    print(f"Action: {proposal['action'][:100]}...")
    print()

    # Stage 6: REPORT
    print("--- Stage 6: REPORT (write cycle_<N>.md) ---")
    report_path = write_cycle_report(
        cycle_n, discovery_summary, acid_test_results,
        cycle_entry, gap, proposal,
    )
    print(f"Wrote: {report_path}")
    print()

    # Stage 7: COMMIT (optional)
    if commit:
        print("--- Stage 7: COMMIT ---")
        ok = git_commit_cycle(cycle_n, report_path, cycle_entry, push=push)
        if ok:
            print(f"Committed cycle {cycle_n}")
            if push:
                print(f"Pushed to origin/main")
        else:
            print(f"Commit failed — see git output above")
        print()

    print("=" * 70)
    print(f"CYCLE {cycle_n:03d} COMPLETE")
    print(f"  Pass: {pass_count}/8 acid tests")
    print(f"  Hardens: {'YES' if pass_count >= 4 else 'NO'}")
    print(f"  Next gap: {gap.get('test', '(none)')}")
    print(f"  Report: {_safe_relative(report_path, ROOT)}")
    print("=" * 70)

    return {
        "cycle": cycle_n,
        "entry": cycle_entry,
        "gap": gap,
        "proposal": proposal,
        "report_path": str(report_path),
        "committed": commit,
    }


def main():
    parser = argparse.ArgumentParser(description="Run one Maestro Loop cycle.")
    parser.add_argument("--commit", action="store_true",
                        help="git add + commit the cycle report")
    parser.add_argument("--push", action="store_true",
                        help="git push after commit (implies --commit)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run stages 1-2 only; do not write or commit")
    args = parser.parse_args()

    result = run_one_cycle(
        commit=args.commit or args.push,
        push=args.push,
        dry_run=args.dry_run,
    )
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
