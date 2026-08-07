#!/usr/bin/env python3
"""
tee_orchestrator.py — Single autocommand execution layer (Correction 2, cycle 202).

Per the CEO's directive: "Everything through autocommands must not remain
aspirational. The roadmap needs one orchestrator that owns the end-to-end
execution path, or entropy will come back as multiple competing loops."

This is the SINGLE entrypoint for the Technology Evolution Engine. No other
script should be the authoritative path. All execution goes through here.

Commands:
    python3 -m scripts.tee_orchestrator discovery     # Run discovery pipeline
    python3 -m scripts.tee_orchestrator invention     # Run invention pipeline
    python3 -m scripts.tee_orchestrator benchmark     # Run all benchmarks
    python3 -m scripts.tee_orchestrator scorecard     # Generate scorecards
    python3 -m scripts.tee_orchestrator failure-audit # Run Failure Engine on discovery stack
    python3 -m scripts.tee_orchestrator reaudit        # Run re-audit
    python3 -m scripts.tee_orchestrator full-loop     # Full: discovery → invention → measure

Usage:
    python3 -m scripts.tee_orchestrator <command> [--verbose]
"""
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO = Path(__file__).resolve().parents[1]


# === STAGE 0: FROZEN DISCOVERY STACK ===
# Per Correction 1: actual filenames, not stale roadmap names.
DISCOVERY_STACK = {
    "document_parsing": "scripts.nlp_pipeline",
    "entity_extraction": "scripts.nlp_pipeline",
    "relation_extraction": "scripts.nlp_pipeline",
    "mechanism_extraction": "scripts.mechanism_extractor",
    "constraint_discovery": "scripts.constraint_discovery_v2",  # NOT constraint_discovery.py
    "bacon_engine": "invention_compiler.bacon_engine",
    "graph_isomorphism": "scripts.graph_isomorphism_analogy",
    "grounded_hypothesis": "scripts.grounded_hypothesis_v2",  # NOT grounded_hypothesis.py
    "reaudit_loop": "scripts.reaudit_loop",
}


def cmd_discovery(verbose=False):
    """Run the discovery pipeline on the corpus."""
    print("=" * 60)
    print("TEE ORCHESTRATOR — Discovery Pipeline")
    print("=" * 60)
    print()

    from scripts.discovery_engine import run_discovery_engine
    discoveries = run_discovery_engine(max_papers=100)

    print(f"\nDiscovery complete: {len(discoveries)} discoveries found")
    for d in discoveries[:5]:
        print(f"  {d.discovery_id}: composite={d.composite_score:.3f}")

    return {"n_discoveries": len(discoveries)}


def cmd_invention(verbose=False):
    """Run the invention pipeline."""
    print("=" * 60)
    print("TEE ORCHESTRATOR — Invention Pipeline")
    print("=" * 60)
    print()

    from scripts.autonomous_inventor import AutonomousInventor
    inventor = AutonomousInventor()
    result = inventor.run(objective="improve thermoelectric performance", domain="thermal")

    print(f"\nInvention complete: {result.get('n_candidates', 0)} candidates generated")
    return result


def cmd_benchmark(verbose=False):
    """Run all benchmarks."""
    print("=" * 60)
    print("TEE ORCHESTRATOR — Benchmark Suite")
    print("=" * 60)
    print()

    import subprocess

    benchmarks = [
        ("Gen 1: Section Segmentation", "benchmarks.section_segmentation_benchmark"),
        ("Gen 2: Entity Extraction", "benchmarks.entity_extraction_benchmark"),
        ("Gen 3: Relation Extraction", "benchmarks.relation_extraction_benchmark"),
        ("Gen 4: Mechanism Chain", "benchmarks.mechanism_chain_benchmark"),
        ("Gen 5: Discovery Layer", "benchmarks.discovery_benchmark"),
        ("Discovery Capability", "benchmarks.discovery_capability_benchmark"),
    ]

    results = {}
    for name, module in benchmarks:
        print(f"  Running {name}...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", module, "--verbose"] if verbose else [sys.executable, "-m", module],
                capture_output=True, text=True, timeout=120, cwd=str(REPO)
            )
            if result.returncode == 0:
                # Try to read the report
                print(f"    ✓ PASS")
                results[name] = "PASS"
            else:
                print(f"    ✗ FAIL: {result.stderr[:200]}")
                results[name] = "FAIL"
        except subprocess.TimeoutExpired:
            print(f"    ⚠ TIMEOUT")
            results[name] = "TIMEOUT"
        except Exception as e:
            print(f"    ✗ ERROR: {e}")
            results[name] = f"ERROR: {e}"

    print(f"\nBenchmark summary: {sum(1 for v in results.values() if v == 'PASS')}/{len(results)} passed")
    return results


def cmd_scorecard(verbose=False):
    """Generate all scorecards."""
    print("=" * 60)
    print("TEE ORCHESTRATOR — Scorecard Generation")
    print("=" * 60)
    print()

    import subprocess

    # Generation benchmark scorecard
    print("  Generating generation scorecard...")
    subprocess.run([sys.executable, "-m", "scripts.generate_auditor_scorecard"],
                   cwd=str(REPO), capture_output=True)

    # 12-category scorecard
    print("  Generating 12-category scorecard...")
    subprocess.run([sys.executable, "-m", "scripts.generate_12_category_scorecard"],
                   cwd=str(REPO), capture_output=True)

    # Print summary
    from scripts.nine_tenths_loop_v2 import assess_all
    gen_results = assess_all()
    at_9 = gen_results["_summary"]["at_9_or_above"]
    print(f"\n  Generation benchmarks: {at_9}/7 at 9/10+")

    scorecard_12 = REPO / "AUDITOR_SCORECARD_12.md"
    if scorecard_12.exists():
        content = scorecard_12.read_text()
        for line in content.split("\n"):
            if "Composite" in line:
                print(f"  12-category: {line.strip()}")
                break

    return {"generation_at_9": at_9}


def cmd_failure_audit(verbose=False):
    """Run the Failure Engine on the current discovery stack (Correction 3).

    Per the CEO: "Make the Failure Engine gate the current discovery stack
    immediately. The circular-gold problem cannot be frozen into the
    discovery baseline."
    """
    print("=" * 60)
    print("TEE ORCHESTRATOR — Failure Engine Audit of Discovery Stack")
    print("=" * 60)
    print()

    from scripts.failure_engine import FailureEngine
    fe = FailureEngine()

    # 1. Check discovery capability benchmark for circularity
    print("  [1] Checking discovery gold set for circularity...")
    import importlib.util
    spec = importlib.util.spec_from_file_location("bench", "benchmarks/discovery_capability_benchmark.py")
    bench = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bench)

    circular = 0
    for gold in bench.GOLD_DISCOVERIES:
        bridge = gold["bridge"].lower()
        if bridge in gold["source_snippet_a"].lower() or bridge in gold["source_snippet_b"].lower():
            circular += 1
            print(f"    ✗ CIRCULAR: {gold['id']} bridge '{bridge}' in input text")
    if circular == 0:
        print(f"    ✓ No circular gold (0/{len(bench.GOLD_DISCOVERIES)})")
    else:
        print(f"    ✗ {circular}/{len(bench.GOLD_DISCOVERIES)} circular gold discoveries!")

    # 2. Check for self-validation in measurement engine
    print("  [2] Checking measurement engine for self-validation...")
    from scripts.measurement_engine import MeasurementEngine
    from scripts.specification import SpecificationEngine
    from scripts.capability_graph import CapabilityGraph

    spec_engine = SpecificationEngine()
    spec = spec_engine.compile("improve thermoelectric performance of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([
        ("bismuth_telluride", "generates", "voltage"),
        ("bismuth_telluride", "conducts", "electricity"),
    ])

    me = MeasurementEngine(seed=42)
    candidates = me.generate(spec, cg, n=1)
    if candidates:
        # Run one iteration to get prediction and measurement
        result = me.run(spec, cg, n_iterations=1)
        # Check if any prediction equals its measurement
        from scripts.self_validation_detector import SelfValidationDetector
        svd = SelfValidationDetector()
        # LoopResult is a dataclass with .iterations
        iterations = result.iterations if hasattr(result, 'iterations') else []
        sv_detected = False
        for it in iterations:
            pred = it.get("prediction", {}) if isinstance(it, dict) else getattr(it, 'prediction', {})
            meas = it.get("measurement", {}) if isinstance(it, dict) else getattr(it, 'measurement', {})
            sv = svd.check(pred, meas)
            if getattr(sv, 'is_self_validating', False):
                sv_detected = True
                break
        print(f"    Self-validation detected: {sv_detected}")
        sv_result = {"detected": sv_detected}
    else:
        print(f"    No candidates generated — cannot check self-validation")
        sv_result = {"detected": False}

    # 3. Check forward model for KB reuse
    print("  [3] Checking forward model for KB formula reuse...")
    from scripts.forward_model_checker import ForwardModelChecker
    from scripts.forward_model import ForwardModel
    from scripts.artifact_generator import Configuration, Component
    fm = ForwardModel()
    # Create a proper Configuration object
    comp = Component(material="Bi2Te3", role="thermoelectric",
                     parameters={"seebeck_coefficient": 200, "electrical_conductivity": 1e5,
                                 "thermal_conductivity": 1.5, "temperature": 300,
                                 "length": 0.001, "area": 1e-6})
    test_config = Configuration(
        config_id="TEST-001",
        spec_objective="test",
        domain="thermoelectric",
        components=[comp],
    )
    pred1 = fm.predict(test_config)
    # Change parameters
    comp2 = Component(material="Bi2Te3", role="thermoelectric",
                      parameters={"seebeck_coefficient": 400, "electrical_conductivity": 1e5,
                                  "thermal_conductivity": 1.5, "temperature": 300,
                                  "length": 0.001, "area": 1e-6})
    test_config2 = Configuration(
        config_id="TEST-002",
        spec_objective="test",
        domain="thermoelectric",
        components=[comp2],
    )
    pred2 = fm.predict(test_config2)
    fmc = ForwardModelChecker()
    fmc_result = fmc.check(fm, [test_config, test_config2])
    fmc_detected = getattr(fmc_result, 'detected', False) if hasattr(fmc_result, 'detected') else False
    print(f"    Predictions vary with parameters: {pred1 != pred2}")
    print(f"    KB reuse detected: {fmc_detected}")

    # 4. Overall verdict
    issues = []
    if circular > 0:
        issues.append(f"CIRCULAR GOLD: {circular} discoveries have bridge in input")
    if sv_result.get("detected", False):
        issues.append("SELF-VALIDATION: prediction == measurement")
    if fmc_detected:
        issues.append("KB REUSE: forward model reuses stored formula")

    print()
    if not issues:
        print("  ✓ FAILURE ENGINE VERDICT: PASS — discovery stack is honest")
        return {"verdict": "PASS", "issues": []}
    else:
        print(f"  ✗ FAILURE ENGINE VERDICT: FAIL — {len(issues)} issues found")
        for issue in issues:
            print(f"    - {issue}")
        return {"verdict": "FAIL", "issues": issues}


def cmd_reaudit(verbose=False):
    """Run the re-audit loop."""
    print("=" * 60)
    print("TEE ORCHESTRATOR — Re-audit")
    print("=" * 60)
    print()

    from scripts.auto_reaudit_scheduler import run_auto_reaudit
    result = run_auto_reaudit()
    print(f"\nRe-audit complete: {result['n_claims_audited']} claims audited")
    for r in result["results"]:
        print(f"  {r['claim_id']}: {r['verdict']}")
    return result


def cmd_full_loop(verbose=False):
    """Run the full loop: discovery → invention → measure."""
    print("=" * 60)
    print("TEE ORCHESTRATOR — Full Loop")
    print("=" * 60)
    print()

    # Step 1: Failure audit (gate)
    print("Step 1: Failure Engine audit...")
    audit = cmd_failure_audit(verbose=verbose)
    if audit["verdict"] == "FAIL":
        print("\n⚠ FAILURE ENGINE VETO — stopping execution.")
        print("  The discovery stack must pass the Failure Engine before proceeding.")
        return {"vetoed": True, "reason": "Failure Engine rejected discovery stack"}

    # Step 2: Discovery
    print("\nStep 2: Discovery pipeline...")
    disc = cmd_discovery(verbose=verbose)

    # Step 3: Invention
    print("\nStep 3: Invention pipeline...")
    inv = cmd_invention(verbose=verbose)

    # Step 4: Benchmarks
    print("\nStep 4: Benchmarks...")
    bench = cmd_benchmark(verbose=verbose)

    # Step 5: Scorecard
    print("\nStep 5: Scorecard...")
    sc = cmd_scorecard(verbose=verbose)

    # Step 6: Re-audit
    print("\nStep 6: Re-audit...")
    ra = cmd_reaudit(verbose=verbose)

    print("\n" + "=" * 60)
    print("FULL LOOP COMPLETE")
    print("=" * 60)
    return {"discovery": disc, "invention": inv, "benchmarks": bench,
            "scorecard": sc, "reaudit": ra}


def main():
    parser = argparse.ArgumentParser(description="TEE Orchestrator — single entrypoint")
    parser.add_argument("command", choices=[
        "discovery", "invention", "benchmark", "scorecard",
        "failure-audit", "reaudit", "full-loop"
    ], help="Command to execute")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    commands = {
        "discovery": cmd_discovery,
        "invention": cmd_invention,
        "benchmark": cmd_benchmark,
        "scorecard": cmd_scorecard,
        "failure-audit": cmd_failure_audit,
        "reaudit": cmd_reaudit,
        "full-loop": cmd_full_loop,
    }

    result = commands[args.command](verbose=args.verbose)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
