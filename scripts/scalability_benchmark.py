#!/usr/bin/env python3
"""
scalability_benchmark.py — Phase 5: measure discovery loop at 1x scale.

Per External Auditor cycle 60:
  "Run discovery loop at 1x scale — record baseline: wall-clock time
   per step, memory, result counts. Commit to
   benchmarks/reports/scalability_1x.json. The 10x and 50x benchmarks
   compare against this."

  "Profile the Swanson triple-nested loop — the External Auditor flagged
   this as a scaling risk. Estimate time at 10x (400 docs → ~4,000 edges
   → potentially 256,000+ bridge candidates if O(n³)). If unreasonable
   (>1 hour), rewrite with indexing."

This script:
  1. Runs the full discovery pipeline at current (1x) corpus size
  2. Records wall-clock time per step (extraction, graph build, Swanson, Gentner, Altshuller, BACON)
  3. Records memory usage (RSS)
  4. Records result counts (nodes, edges, bridges, analogies, contradictions)
  5. Estimates time at 10x and 50x using O(n) / O(n²) / O(n³) scaling models
  6. Flags any step that would take >1 hour at 10x or 50x

Per No-Gaming Rule (FA3): this benchmark runs on REAL documents only.
No synthetic data. The 1x corpus is the real papers + patents + RC papers
already in data/ingestion/.
"""
import sys
import pathlib
import json
import time
import tracemalloc
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def measure_1x_baseline() -> dict:
    """Run the full discovery pipeline at 1x scale and measure everything."""
    print("=" * 70)
    print("PHASE 5 — Scalability Benchmark at 1x scale")
    print("=" * 70)
    print()

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scale": "1x",
        "corpus": {},
        "steps": {},
        "estimates": {},
    }

    # Step 0: Count corpus
    papers = list((ROOT / "data" / "ingestion" / "papers").glob("*.txt"))
    patents = list((ROOT / "data" / "ingestion" / "patents").glob("*.txt"))
    rc = list((ROOT / "data" / "ingestion" / "radiative_cooling").glob("*.txt"))
    sib = list((ROOT / "data" / "ingestion" / "sib_corpus").glob("*.txt"))
    real = list((ROOT / "data" / "ingestion" / "real").glob("*.txt"))

    total_docs = len(papers) + len(patents) + len(rc) + len(sib) + len(real)
    results["corpus"] = {
        "papers": len(papers),
        "patents": len(patents),
        "radiative_cooling": len(rc),
        "sib_corpus": len(sib),
        "real": len(real),
        "total": total_docs,
    }
    print(f"Corpus: {total_docs} documents")
    print(f"  papers={len(papers)}, patents={len(patents)}, RC={len(rc)}, SIB={len(sib)}, real={len(real)}")
    print()

    # Start memory tracking
    tracemalloc.start()

    # Step 1: Edge extraction
    print("--- Step 1: Edge extraction ---")
    t0 = time.time()
    from invention_compiler.edge_extractor import EdgeExtractor
    extractor = EdgeExtractor()

    paper_graph = extractor.extract_from_corpus(str(ROOT / "data" / "ingestion" / "papers"), use_discovery_graph=False)
    patent_graph = extractor.extract_from_corpus(str(ROOT / "data" / "ingestion" / "patents"), use_discovery_graph=False)
    rc_graph = extractor.extract_from_corpus(str(ROOT / "data" / "ingestion" / "radiative_cooling"), use_discovery_graph=False)
    sib_graph = extractor.extract_from_corpus(str(ROOT / "data" / "ingestion" / "sib_corpus"), use_discovery_graph=False)
    real_graph = extractor.extract_from_corpus(str(ROOT / "data" / "ingestion" / "real"), use_discovery_graph=False)

    t1 = time.time()
    current, peak = tracemalloc.get_traced_memory()
    results["steps"]["extraction"] = {
        "wall_clock_s": round(t1 - t0, 3),
        "memory_mb": round(peak / 1e6, 2),
        "docs_processed": total_docs,
    }
    print(f"  time: {t1-t0:.3f}s, memory: {peak/1e6:.2f} MB")

    # Merge graphs
    combined = type(paper_graph)()
    for src in (paper_graph, patent_graph, rc_graph, sib_graph, real_graph):
        for nid, node in src.nodes.items():
            if nid not in combined.nodes:
                combined.add_node(node)
        for edge in src.edges:
            exists = any(e.source == edge.source and e.target == edge.target and e.mechanism == edge.mechanism for e in combined.edges)
            if not exists:
                combined.add_edge(edge)

    results["graph"] = {
        "nodes": len(combined.nodes),
        "edges": len(combined.edges),
    }
    print(f"  graph: {len(combined.nodes)} nodes, {len(combined.edges)} edges")

    # Step 2: Build DiscoveryGraph
    print("--- Step 2: Build DiscoveryGraph ---")
    t0 = time.time()
    dg = combined.to_discovery_graph()
    t1 = time.time()
    current, peak = tracemalloc.get_traced_memory()
    results["steps"]["graph_build"] = {
        "wall_clock_s": round(t1 - t0, 3),
        "memory_mb": round(peak / 1e6, 2),
    }
    print(f"  time: {t1-t0:.3f}s, memory: {peak/1e6:.2f} MB")

    # Step 3: Swanson bridge search
    print("--- Step 3: Swanson bridge search ---")
    from invention_compiler.discovery_graph import SwansonBridgeSearch, GentnerStructureMapping, AltshullerContradictionSearch
    t0 = time.time()
    bridges = SwansonBridgeSearch.search(dg)
    t1 = time.time()
    current, peak = tracemalloc.get_traced_memory()
    results["steps"]["swanson"] = {
        "wall_clock_s": round(t1 - t0, 3),
        "memory_mb": round(peak / 1e6, 2),
        "bridges_found": len(bridges),
        "edges_in_graph": len(combined.edges),
    }
    print(f"  time: {t1-t0:.3f}s, bridges: {len(bridges)}, memory: {peak/1e6:.2f} MB")

    # Step 4: Gentner structure mapping
    print("--- Step 4: Gentner structure mapping ---")
    t0 = time.time()
    analogies = GentnerStructureMapping.find_analogous_chains(dg, min_chain_length=2)
    t1 = time.time()
    current, peak = tracemalloc.get_traced_memory()
    results["steps"]["gentner"] = {
        "wall_clock_s": round(t1 - t0, 3),
        "memory_mb": round(peak / 1e6, 2),
        "analogies_found": len(analogies),
    }
    print(f"  time: {t1-t0:.3f}s, analogies: {len(analogies)}, memory: {peak/1e6:.2f} MB")

    # Step 5: Altshuller contradiction search
    print("--- Step 5: Altshuller contradiction search ---")
    t0 = time.time()
    contradictions = AltshullerContradictionSearch.find_contradictions(dg)
    t1 = time.time()
    current, peak = tracemalloc.get_traced_memory()
    results["steps"]["altshuller"] = {
        "wall_clock_s": round(t1 - t0, 3),
        "memory_mb": round(peak / 1e6, 2),
        "contradictions_found": len(contradictions),
    }
    print(f"  time: {t1-t0:.3f}s, contradictions: {len(contradictions)}, memory: {peak/1e6:.2f} MB")

    # Step 6: BACON (on real data)
    print("--- Step 6: BACON law discovery ---")
    t0 = time.time()
    from invention_compiler.bacon_engine import discover_law, stefan_boltzmann_dataset
    sb_data = stefan_boltzmann_dataset(n_points=15)
    law = discover_law(sb_data["T_surface_K"], sb_data["Q_W"])
    t1 = time.time()
    current, peak = tracemalloc.get_traced_memory()
    results["steps"]["bacon"] = {
        "wall_clock_s": round(t1 - t0, 3),
        "memory_mb": round(peak / 1e6, 2),
        "law_found": law is not None,
        "r2": law.r2 if law else None,
    }
    law_r2 = f"{law.r2:.4f}" if law else "None"
    print(f"  time: {t1-t0:.3f}s, law R²={law_r2}, memory: {peak/1e6:.2f} MB")

    tracemalloc.stop()

    # Total time
    total_time = sum(s["wall_clock_s"] for s in results["steps"].values())
    results["total_wall_clock_s"] = round(total_time, 3)
    print(f"\nTotal wall-clock: {total_time:.3f}s")

    # Scaling estimates
    print("\n--- Scaling estimates ---")
    n_edges = len(combined.edges)
    n_nodes = len(dg.nodes)
    swanson_time = results["steps"]["swanson"]["wall_clock_s"]
    gentner_time = results["steps"]["gentner"]["wall_clock_s"]

    # Swanson: triple-nested loop over edges → O(n³) worst case
    # At 1x: n edges → swanson_time
    # At 10x: 10n edges → 1000 × swanson_time (if O(n³))
    # At 50x: 50n edges → 125000 × swanson_time (if O(n³))
    for scale, factor in [("10x", 10), ("50x", 50)]:
        est_swanson = swanson_time * (factor ** 3)
        est_gentner = gentner_time * (factor ** 2)  # Gentner is O(n²) chain comparison
        results["estimates"][scale] = {
            "est_edges": n_edges * factor,
            "est_swanson_s": round(est_swanson, 1),
            "est_swanson_min": round(est_swanson / 60, 1),
            "est_gentner_s": round(est_gentner, 1),
            "est_gentner_min": round(est_gentner / 60, 1),
            "swanson_unreasonable": est_swanson > 3600,  # >1 hour
            "gentner_unreasonable": est_gentner > 3600,
        }
        print(f"  {scale} ({n_edges * factor} edges):")
        print(f"    Swanson est: {est_swanson:.1f}s ({est_swanson/60:.1f} min) — {'UNREASONABLE (>1h)' if est_swanson > 3600 else 'OK'}")
        print(f"    Gentner est: {est_gentner:.1f}s ({est_gentner/60:.1f} min) — {'UNREASONABLE (>1h)' if est_gentner > 3600 else 'OK'}")

    # Flag algorithms needing rewrite
    needs_rewrite = []
    for scale in ("10x", "50x"):
        if results["estimates"][scale]["swanson_unreasonable"]:
            needs_rewrite.append(f"Swanson at {scale} (est. {results['estimates'][scale]['est_swanson_min']:.1f} min)")
        if results["estimates"][scale]["gentner_unreasonable"]:
            needs_rewrite.append(f"Gentner at {scale} (est. {results['estimates'][scale]['est_gentner_min']:.1f} min)")
    results["needs_rewrite"] = needs_rewrite
    if needs_rewrite:
        print(f"\n  ⚠️  Algorithms needing rewrite: {needs_rewrite}")
    else:
        print(f"\n  ✅ No algorithms need rewrite at 10x or 50x")

    # Write benchmark file
    reports_dir = ROOT / "benchmarks" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    benchmark_path = reports_dir / "scalability_1x.json"
    benchmark_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nBenchmark written: {benchmark_path.relative_to(ROOT)}")

    return results


if __name__ == "__main__":
    measure_1x_baseline()
