"""
Formula-to-edge promotion module.

Per DR-7: when a formula is executed and matches the stated output,
the edge's mechanism_status should be promoted from ASSERTED to
VERIFIED (specifically: DERIVED if first-principles, SIMULATED if
numerically computed, OBSERVED if experimentally reproduced).

This module connects Layer 2 (formula verifier) to Layer 3 (causal
simulator) by promoting edges in the causal graph based on formula
verification results.

Per F-061: "VERIFIED tier is empty" — this module fills it.
"""
import sys
import pathlib
from typing import Dict, Any, List, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.causal_graph import (
    CausalEdge, CausalNode, CausalGraph, EdgeTier, MechanismStatus,
)
from scripts.verify_formulas import run_all_verifications


def promote_edges_from_formula_results(
    graph,
    formula_results: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Promote ASSERTED edges to VERIFIED based on formula verification.

    Per Law 28 (cycle 39): accepts either CausalGraph (deprecated) or
    DiscoveryGraph (canonical). If DiscoveryGraph, promotes edges in the
    CausalGraphLayer subgraph.

    For each formula that PASSES (computed output matches expected within
    tolerance), find the corresponding edge in the causal graph and promote
    its mechanism_status from ASSERTED to DERIVED (since the formula was
    derived from first principles and executed as a callable function).

    IMPORTANT: promotion is per-edge, not per-formula. An edge is promoted
    only if the formula's computed output for THAT EDGE'S specific inputs
    matches the edge's stated expected_output within tolerance. A formula
    that passes on one set of inputs may fail on another — only the
    matching edge gets promoted.

    Args:
        graph: a CausalGraph (deprecated) or DiscoveryGraph (canonical)
        formula_results: results from verify_formulas.run_all_verifications().
                         If None, runs the verification fresh.

    Returns:
        A dict with: total_edges, promoted, already_verified, not_promotable,
        promotion_details
    """
    if formula_results is None:
        formula_results = run_all_verifications()

    # Handle DiscoveryGraph (Law 28 canonical) — use the causal subgraph's edges
    # but preserve the DiscoveryGraph reference for cross-layer queries
    if hasattr(graph, 'causal') and hasattr(graph, 'import_causal_graph'):
        # DiscoveryGraph — operate on its causal layer's edges
        edges = graph.causal.edges
    else:
        # CausalGraph (deprecated) — use edges directly
        edges = graph.edges

    # Build a map of (formula_name, inputs_key, expected_output, tolerance) → passed status
    # This allows per-edge promotion: only edges whose specific inputs AND
    # expected_output match a passing test case get promoted.
    # A formula that passes for inputs (T=42, RH=25) with expected=25.8
    # should NOT promote an edge with inputs (T=42, RH=25) but expected=19.0.
    formula_input_results = {}
    for r in formula_results:
        name = r["formula_name"]
        inputs_key = tuple(sorted(r["inputs"].items()))
        expected = r["expected_output"]
        tol = r["tolerance"]
        key = (name, inputs_key, expected, tol)
        formula_input_results[key] = r["passed"]

    promoted = 0
    already_verified = 0
    not_promotable = 0
    details = []

    for edge in edges:
        if edge.tier == EdgeTier.VERIFIED:
            already_verified += 1
            continue

        if edge.tier == EdgeTier.ASSOCIATIVE:
            not_promotable += 1
            continue

        # ASSERTED edge — check if it has a formula that passed
        # for THIS EDGE'S specific inputs
        if edge.formula and edge.formula_inputs:
            # Check if this specific input set has a passing result
            edge_inputs_key = tuple(sorted(edge.formula_inputs.items()))
            lookup_key = (edge.formula, edge_inputs_key, edge.expected_output, edge.tolerance)

            if lookup_key in formula_input_results:
                if formula_input_results[lookup_key]:
                    # The formula was executed for these exact inputs and matched
                    edge.tier = EdgeTier.VERIFIED
                    edge.mechanism_status = MechanismStatus.DERIVED
                    promoted += 1
                    details.append({
                        "edge": f"{edge.source} → {edge.target}",
                        "formula": edge.formula,
                        "inputs": edge.formula_inputs,
                        "promotion": "ASSERTED → VERIFIED (DERIVED)",
                        "reason": f"Formula '{edge.formula}' executed for inputs {edge.formula_inputs} and matched expected output within tolerance",
                    })
                else:
                    # GAP-002: formula FAILED for these inputs — mark CONTRADICTED
                    edge.tier = EdgeTier.CONTRADICTED
                    edge.mechanism_status = MechanismStatus.CONTRADICTED
                    not_promotable += 1
                    details.append({
                        "edge": f"{edge.source} → {edge.target}",
                        "formula": edge.formula,
                        "inputs": edge.formula_inputs,
                        "promotion": "ASSERTED → CONTRADICTED",
                        "reason": f"Formula '{edge.formula}' executed for inputs {edge.formula_inputs} and FAILED — computed output does not match stated expected output. This edge is actively wrong, not merely unverified.",
                    })
            else:
                # The formula exists but wasn't tested with these specific inputs.
                # Execute the formula directly for this edge's inputs.
                # Import the formula module and call it.
                try:
                    if edge.formula == "stull_wet_bulb":
                        from scripts.formulas.stull_wet_bulb import verify as verify_fn
                    elif edge.formula == "stefan_boltzmann":
                        from scripts.formulas.stefan_boltzmann import verify as verify_fn
                    elif edge.formula == "pcm_latent_heat":
                        from scripts.formulas.pcm_latent_heat import verify as verify_fn
                    else:
                        not_promotable += 1
                        continue

                    passed, computed, msg = verify_fn(
                        edge.formula_inputs,
                        edge.expected_output if edge.expected_output is not None else 0,
                        edge.tolerance if edge.tolerance is not None else 0.5,
                    )
                    if passed:
                        edge.tier = EdgeTier.VERIFIED
                        edge.mechanism_status = MechanismStatus.DERIVED
                        promoted += 1
                        details.append({
                            "edge": f"{edge.source} → {edge.target}",
                            "formula": edge.formula,
                            "inputs": edge.formula_inputs,
                            "promotion": "ASSERTED → VERIFIED (DERIVED)",
                            "reason": f"Formula executed on-demand: {msg}",
                        })
                    else:
                        # GAP-002: on-demand execution FAILED — mark CONTRADICTED
                        edge.tier = EdgeTier.CONTRADICTED
                        edge.mechanism_status = MechanismStatus.CONTRADICTED
                        not_promotable += 1
                        details.append({
                            "edge": f"{edge.source} → {edge.target}",
                            "formula": edge.formula,
                            "inputs": edge.formula_inputs,
                            "promotion": "ASSERTED → CONTRADICTED",
                            "reason": f"Formula executed on-demand and FAILED: {msg}",
                        })
                except Exception as e:
                    not_promotable += 1
                    details.append({
                        "edge": f"{edge.source} → {edge.target}",
                        "formula": edge.formula,
                        "inputs": edge.formula_inputs,
                        "promotion": "ERROR",
                        "reason": f"Could not execute formula: {e}",
                    })
        else:
            not_promotable += 1

    return {
        "total_edges": len(edges),
        "promoted": promoted,
        "already_verified": already_verified,
        "not_promotable": not_promotable,
        "promotion_details": details,
        "causal_density_after": graph.causal_density() if hasattr(graph, 'causal_density') else 0.0,
        "tier_counts_after": graph.tier_counts() if hasattr(graph, 'tier_counts') else {},
    }


def verify_and_promote(graph) -> Dict[str, Any]:
    """Run formula verification and promote matching edges.

    This is the full Layer 2 → Layer 3 integration:
    1. Execute all formulas (Layer 2)
    2. For each formula that passes, promote the corresponding edge (Layer 3)
    3. Report the new causal density (verified / total edges)

    The causal density is the metric that measures how much of the graph
    is actually causal vs. how much is asserted or associative. After
    promotion, the density should increase.
    """
    results = run_all_verifications()
    promotion_result = promote_edges_from_formula_results(graph, results)

    return {
        "formula_results": results,
        "promotion_result": promotion_result,
        "causal_density_before": promotion_result["causal_density_after"],  # already updated
        "tier_counts": promotion_result["tier_counts_after"],
    }
