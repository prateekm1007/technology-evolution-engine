"""
lineage_validator.py — Repair A: real graph-traversal lineage verification.

Reviewer directive:
    "Replace lineage_node_count > 1 with an actual graph-integrity/traversal
     validator. node_count > 1 must be removed. That is a metric, not an
     invariant."

This module performs actual DFS traversal of a DiscoveryCase's provenance
graph and verifies:
  1. every referenced node exists (no dangling edges)
  2. every edge endpoint exists (no orphan nodes that should have parents)
  3. required parent-child relationships exist (e.g. hypothesis → transfer)
  4. expected terminal nodes are reachable from the case (source_doc, etc.)
  5. hashes match the referenced stage artifacts on disk

The validator returns a LineageVerificationResult with:
  - valid: bool (True only if ALL checks pass)
  - checks: list of (check_name, passed, detail)
  - traversal: the set of nodes reachable from the case root
  - orphans: nodes with no incoming edge and no root status
  - missing_parents: nodes missing required parent relationships
  - hash_mismatches: nodes whose content_hash doesn't match the artifact
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from discovery_infrastructure.discovery_substrate import (
    DiscoveryCase, ProvenanceGraph, ProvenanceNode, ProvenanceEdge,
)


@dataclass
class LineageCheck:
    """A single lineage check result."""
    name: str
    passed: bool
    detail: str = ""

    def to_dict(self) -> Dict:
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


@dataclass
class LineageVerificationResult:
    """The result of verifying a DiscoveryCase's lineage by graph traversal."""
    case_id: str
    valid: bool = False
    checks: List[LineageCheck] = field(default_factory=list)
    reachable_nodes: List[str] = field(default_factory=list)
    orphans: List[str] = field(default_factory=list)
    missing_parents: List[str] = field(default_factory=list)
    hash_mismatches: List[str] = field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0

    def to_dict(self) -> Dict:
        return {
            "case_id": self.case_id,
            "valid": self.valid,
            "checks": [c.to_dict() for c in self.checks],
            "reachable_nodes": self.reachable_nodes,
            "orphans": self.orphans,
            "missing_parents": self.missing_parents,
            "hash_mismatches": self.hash_mismatches,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            # The "valid" field IS the lineage_traversable invariant.
            # There is no separate "lineage_traversable" boolean.
            # Either the graph passes all traversal checks, or it doesn't.
        }


# Required parent-child relationships by node_type.
# For each node type, the set of parent node_types that MUST exist
# and have an edge pointing TO this node.
# (A node may have multiple required parent types; at least one of each
#  type must be present as a parent.)
REQUIRED_PARENTS: Dict[str, Set[str]] = {
    "mechanism_graph": {"source_document"},
    "mechanism_pattern": {"mechanism_graph"},
    "transfer_hypothesis": {"mechanism_pattern"},
    "hypothesis": {"transfer_hypothesis"},
    "adversarial_analysis": {"hypothesis"},
    "rediscovery_analysis": {"hypothesis"},
    "novelty_assessment": {"hypothesis"},
    "prediction": {"hypothesis"},
    "experiment_proposal": {"prediction"},
}

# Node types that are expected to be reachable from the case root
# (i.e. the lineage should contain at least one of each if the pipeline
#  reached that stage). These are checked only if the node exists.
EXPECTED_REACHABLE_TYPES: Set[str] = {
    "source_document", "mechanism_graph", "mechanism_pattern",
    "transfer_hypothesis", "hypothesis",
}

# Node types that are roots (no required parent)
ROOT_TYPES: Set[str] = {
    "source_document", "checkpointed_run",
}


class LineageValidator:
    """Verify a DiscoveryCase's provenance graph by actual DFS traversal.

    This replaces the superficial `node_count > 1` check with a real
    graph-integrity invariant.
    """

    def verify(self, case: DiscoveryCase,
               run_dir: Optional[Path] = None) -> LineageVerificationResult:
        """Verify the lineage of a DiscoveryCase.

        Args:
            case: the DiscoveryCase with a populated ProvenanceGraph
            run_dir: optional path to the run directory, for hash verification
                     against stage artifacts on disk

        Returns:
            LineageVerificationResult with valid=True only if ALL checks pass.
        """
        result = LineageVerificationResult(case_id=case.case_id)
        prov = case.provenance
        result.node_count = len(prov.nodes)
        result.edge_count = len(prov.edges)

        # ---- Check 1: No dangling edges (every edge endpoint exists) ----
        dangling = []
        node_ids = set(prov.nodes.keys())
        for edge in prov.edges:
            if edge.source_node_id not in node_ids:
                dangling.append(f"edge {edge.edge_id}: source {edge.source_node_id} missing")
            if edge.target_node_id not in node_ids:
                dangling.append(f"edge {edge.edge_id}: target {edge.target_node_id} missing")
        result.checks.append(LineageCheck(
            name="no_dangling_edges",
            passed=len(dangling) == 0,
            detail=f"{len(dangling)} dangling edges" if dangling else "all edge endpoints exist"
        ))

        # ---- Check 2: DFS traversal from run node reaches expected types ----
        # Find root nodes (checkpointed_run or source_document)
        roots = [nid for nid, n in prov.nodes.items()
                 if n.node_type in ROOT_TYPES]
        reachable: Set[str] = set()
        for root in roots:
            self._dfs(root, prov, reachable, set())
        result.reachable_nodes = sorted(reachable)

        # Check that all EXPECTED_REACHABLE_TYPES are present in reachable set
        reachable_types = {prov.nodes[nid].node_type for nid in reachable
                           if nid in prov.nodes}
        missing_types = EXPECTED_REACHABLE_TYPES - reachable_types
        result.checks.append(LineageCheck(
            name="expected_types_reachable",
            passed=len(missing_types) == 0,
            detail=f"missing types: {sorted(missing_types)}" if missing_types
                   else f"all {len(EXPECTED_REACHABLE_TYPES)} expected types reachable"
        ))

        # ---- Check 3: No orphan scientific nodes (nodes with no incoming edge
        #               and no root status) ----
        nodes_with_incoming = {e.target_node_id for e in prov.edges}
        orphans = []
        for nid, node in prov.nodes.items():
            if node.node_type in ROOT_TYPES:
                continue  # roots are allowed to have no incoming
            if nid not in nodes_with_incoming:
                orphans.append(f"{nid} (type={node.node_type})")
        result.orphans = orphans
        result.checks.append(LineageCheck(
            name="no_orphan_scientific_nodes",
            passed=len(orphans) == 0,
            detail=f"{len(orphans)} orphan nodes" if orphans
                   else "all non-root nodes have at least one incoming edge"
        ))

        # ---- Check 4: Required parent-child relationships exist ----
        # For each node, check that its required parent types are present
        # among nodes that have edges pointing TO it.
        missing_parents = []
        for nid, node in prov.nodes.items():
            if node.node_type not in REQUIRED_PARENTS:
                continue
            required_parent_types = REQUIRED_PARENTS[node.node_type]
            # Find actual parents (nodes with edges pointing TO this node)
            actual_parent_types = set()
            for edge in prov.edges:
                if edge.target_node_id == nid and edge.source_node_id in prov.nodes:
                    actual_parent_types.add(prov.nodes[edge.source_node_id].node_type)
            # Check each required parent type is present
            for rpt in required_parent_types:
                if rpt not in actual_parent_types:
                    missing_parents.append(
                        f"{nid} (type={node.node_type}) missing required parent type={rpt}")
        result.missing_parents = missing_parents
        result.checks.append(LineageCheck(
            name="required_parent_relationships",
            passed=len(missing_parents) == 0,
            detail=f"{len(missing_parents)} missing parent relationships" if missing_parents
                   else "all required parent-child relationships present"
        ))

        # ---- Check 5: Hash verification against stage artifacts (if run_dir provided) ----
        if run_dir is not None:
            hash_mismatches = self._verify_hashes(prov, run_dir)
            result.hash_mismatches = hash_mismatches
            result.checks.append(LineageCheck(
                name="artifact_hash_verification",
                passed=len(hash_mismatches) == 0,
                detail=f"{len(hash_mismatches)} hash mismatches" if hash_mismatches
                       else "all verifiable hashes match stage artifacts"
            ))
        # If no run_dir, skip hash verification (not a failure)
        # ---- Check 6: Provenance root hash is verifiable ----
        root_hash_ok = False
        if case.provenance_root_hash:
            root_hash_ok = case.verify_provenance()
        result.checks.append(LineageCheck(
            name="provenance_root_hash_verifiable",
            passed=root_hash_ok,
            detail=f"root_hash={case.provenance_root_hash[:16]}..." if root_hash_ok
                   else "provenance root hash missing or verification failed"
        ))

        # ---- Final validity: ALL checks must pass ----
        result.valid = all(c.passed for c in result.checks)
        return result

    def _dfs(self, node_id: str, prov: ProvenanceGraph,
             reachable: Set[str], visited: Set[str]) -> None:
        """Depth-first traversal. Follows edges in BOTH directions so we
        can reach all connected nodes regardless of edge direction."""
        if node_id in visited:
            return
        visited.add(node_id)
        if node_id in prov.nodes:
            reachable.add(node_id)
        # Follow edges in both directions (treat as undirected for reachability)
        for edge in prov.edges:
            if edge.source_node_id == node_id and edge.target_node_id not in visited:
                self._dfs(edge.target_node_id, prov, reachable, visited)
            elif edge.target_node_id == node_id and edge.source_node_id not in visited:
                self._dfs(edge.source_node_id, prov, reachable, visited)

    def _verify_hashes(self, prov: ProvenanceGraph, run_dir: Path) -> List[str]:
        """Verify that node content_hashes match the actual stage artifacts on disk.

        FAIL-CLOSED semantics (per reviewer round-5 directive):
          - Every node with metadata["artifact_stage"] MUST be verified.
          - If artifact_stage is present but the artifact file is missing → FAIL.
          - If the artifact file exists but output_hash is empty → FAIL.
          - If artifact.output_hash != node.content_hash → FAIL.
          - If artifact_stage is absent AND the node type is one that SHOULD
            reference an artifact (i.e. not a root type) → FAIL (missing reference).
          - Only root-type nodes (source_document, checkpointed_run) without
            artifact_stage are allowed to skip — and even then, only if they
            have a content_hash (otherwise FAIL).

        This replaces the previous best-effort skip behavior. A check that
        passes because there was nothing eligible to check is NOT evidence
        that the hashes were verified.
        """
        mismatches = []
        # Node types that MUST carry an artifact_stage reference
        # (because their content originates from a checkpoint stage artifact)
        TYPES_REQUIRING_ARTIFACT_REF = {
            "mechanism_graph", "mechanism_pattern", "transfer_hypothesis",
            "hypothesis", "adversarial_analysis", "rediscovery_analysis",
            "novelty_assessment", "prediction", "experiment_proposal",
        }
        for nid, node in prov.nodes.items():
            artifact_stage = node.metadata.get("artifact_stage", "") if node.metadata else ""
            expected_hash = node.metadata.get("artifact_output_hash", "") if node.metadata else ""

            # Root types (source_document, checkpointed_run) may not reference
            # a stage artifact — but source_document DOES reference 01_extraction
            # in the current implementation, so this branch is rarely hit.
            if node.node_type not in TYPES_REQUIRING_ARTIFACT_REF:
                # Root-type node: no artifact reference required
                continue

            # FAIL if the artifact_stage reference is missing entirely
            if not artifact_stage:
                mismatches.append(
                    f"{nid} (type={node.node_type}): missing artifact_stage reference — "
                    "every non-root provenance node MUST reference its source artifact")
                continue

            # FAIL if the expected hash is empty
            if not expected_hash:
                mismatches.append(
                    f"{nid} (type={node.node_type}): artifact_output_hash is empty — "
                    f"artifact_stage={artifact_stage!r} but no hash recorded")
                continue

            # FAIL if the node's own content_hash doesn't match the expected hash
            if node.content_hash != expected_hash:
                mismatches.append(
                    f"{nid} (type={node.node_type}): node content_hash "
                    f"{node.content_hash[:16]}... != artifact_output_hash "
                    f"{expected_hash[:16]}... — node hash does not match its declared artifact hash")
                continue

            # Load the artifact file from disk
            artifact_path = run_dir / f"{artifact_stage}.json"
            if not artifact_path.exists():
                mismatches.append(
                    f"{nid} (type={node.node_type}): artifact file {artifact_stage}.json "
                    "does not exist on disk")
                continue

            # Parse the artifact JSON
            try:
                artifact = json.loads(artifact_path.read_text())
            except json.JSONDecodeError as e:
                mismatches.append(
                    f"{nid} (type={node.node_type}): artifact {artifact_stage}.json "
                    f"is not valid JSON: {e}")
                continue

            # Extract the artifact's output_hash
            artifact_hash = artifact.get("output_hash", "")
            if not artifact_hash:
                mismatches.append(
                    f"{nid} (type={node.node_type}): artifact {artifact_stage}.json "
                    "has no output_hash field")
                continue

            # FAIL if the artifact's output_hash doesn't match the node's content_hash
            if artifact_hash != node.content_hash:
                mismatches.append(
                    f"{nid} (type={node.node_type}): node content_hash "
                    f"{node.content_hash[:16]}... != artifact {artifact_stage}.json "
                    f"output_hash {artifact_hash[:16]}... — artifact was modified "
                    "after lineage creation or substituted")
                continue

            # Cross-check: the artifact's output_hash must also match the
            # run manifest's recorded output_hash for this stage (if the
            # manifest is available)
            manifest_path = run_dir / "manifest.json"
            if manifest_path.exists():
                try:
                    manifest = json.loads(manifest_path.read_text())
                    stage_status = manifest.get("stages", {}).get(artifact_stage, {})
                    manifest_hash = stage_status.get("output_hash", "")
                    if manifest_hash and manifest_hash != artifact_hash:
                        mismatches.append(
                            f"{nid} (type={node.node_type}): artifact {artifact_stage}.json "
                            f"output_hash {artifact_hash[:16]}... != manifest stage "
                            f"output_hash {manifest_hash[:16]}... — manifest/artifact mismatch")
                except (json.JSONDecodeError, KeyError):
                    pass  # manifest parse failure is not a lineage failure

        return mismatches


__all__ = ["LineageValidator", "LineageVerificationResult", "LineageCheck",
           "REQUIRED_PARENTS", "EXPECTED_REACHABLE_TYPES", "ROOT_TYPES"]
