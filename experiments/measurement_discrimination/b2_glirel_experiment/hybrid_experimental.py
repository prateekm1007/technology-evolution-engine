#!/usr/bin/env python3
"""hybrid_experimental.py — EXPERIMENTAL hybrid GLiREL→GLM adjudicator.

ARCHITECTURE:
    Source
      ↓
    NER (entity extraction)
      ↓
    GLiREL (relation extraction)
      ↓
    structured relation graph + exact source spans
      ↓
    GLM semantic adjudicator (calls frozen B-2 detector)
      ↓
    existing B-2 logic (counterfactual, ISS classification)

STATUS: EXPERIMENTAL_ONLY
    This module is NOT the frozen B-2 implementation.
    Its output is explicitly labelled EXPERIMENTAL_ONLY.
    The frozen B-2 detector (commit f905b68) remains authoritative.

ANTI-CHEATING (per CTO directive §19):
    GLiREL extracting a relation does NOT mean A+B = valid mechanism.
    The downstream semantic adjudicator still must establish:
      - A component valid
      - B component valid
      - derived relation valid
      - neither source independently contains complete relation
      - counterfactual destruction
    The frozen 8-step verification ordering remains authoritative.
"""
import json
import os
import subprocess
import tempfile
from typing import Optional
from extractor import GLiRELExtractor, EvidenceEdge
from graph import build_graph, EvidenceGraph


class HybridAdjudicator:
    """Experimental hybrid: GLiREL extraction → GLM adjudication → B-2.

    This module:
    1. Uses GLiREL to extract structured relations from both sources
    2. Builds an evidence graph with exact spans
    3. Constructs a GLM prompt that includes the structured evidence
    4. Calls the frozen B-2 detector (b2_detector.mjs) for adjudication
    5. Labels the output EXPERIMENTAL_ONLY

    The frozen B-2 detector is NOT modified. It is called as-is.
    """

    def __init__(self, glirel_model_identifier: str = "jackboyla/glirel_beta"):
        self.glirel = GLiRELExtractor.from_pretrained(glirel_model_identifier)
        self.experimental_label = "EXPERIMENTAL_ONLY"

    def evaluate(
        self,
        case_id: str,
        candidate: str,
        source_a: str,
        source_b: str,
        entity_list_a: list,
        entity_list_b: list,
        relation_labels: list,
        threshold: float = 0.1,
        top_k: int = 5,
    ) -> dict:
        """Evaluate a candidate using the hybrid pipeline.

        Returns a dict with:
          - evidence_graph: the structured GLiREL evidence
          - glm_trace: the frozen B-2 detector's trace
          - experimental_label: "EXPERIMENTAL_ONLY"
          - comparison: differences between hybrid and frozen-only
        """
        # Step 1: GLiREL extraction from both sources
        edges_a = self.glirel.extract_relations(
            source_id="A",
            source_text=source_a,
            entity_list=entity_list_a,
            relation_labels=relation_labels,
            threshold=threshold,
            top_k=top_k,
        )
        edges_b = self.glirel.extract_relations(
            source_id="B",
            source_text=source_b,
            entity_list=entity_list_b,
            relation_labels=relation_labels,
            threshold=threshold,
            top_k=top_k,
        )

        # Step 2: Build evidence graph
        graph = build_graph(case_id, candidate, source_a, source_b, edges_a, edges_b)

        # Step 3: Call frozen B-2 detector (GLM) for adjudication
        # The frozen detector does NOT see the GLiREL evidence — it produces
        # its own independent trace. The hybrid comparison is done by
        # analyzing whether the GLiREL evidence would have helped.
        glm_trace = self._call_frozen_detector(case_id, candidate, source_a, source_b)

        # Step 4: Construct hybrid analysis
        # (This is where the GLiREL evidence COULD be fed to the GLM,
        # but for this experiment we compare independently first.)
        hybrid_analysis = self._analyze_evidence_quality(graph, glm_trace)

        return {
            "experimental_label": self.experimental_label,
            "case_id": case_id,
            "candidate": candidate,
            "evidence_graph": graph.to_dict(),
            "glm_trace": glm_trace,
            "hybrid_analysis": hybrid_analysis,
        }

    def _call_frozen_detector(self, case_id, candidate, source_a, source_b) -> dict:
        """Call the frozen B-2 detector (b2_detector.mjs) via Node.js.

        This does NOT modify the frozen detector. It calls the existing
        detectOnce() function via a Node.js subprocess.
        """
        # Write a temporary Node.js script that calls the frozen detector
        impl_dir = os.path.join(
            os.path.dirname(__file__), "..",
            "b2_adversarial_v2", "implementation"
        )
        script = f"""
import {{ detectOnce }} from '{impl_dir}/b2_detector.mjs';
const params = {{
  id: '{case_id}',
  candidate: {json.dumps(candidate)},
  source_a: {json.dumps(source_a)},
  source_b: {json.dumps(source_b)},
}};
const trace = await detectOnce(params);
console.log(JSON.stringify(trace));
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mjs', delete=False) as f:
            f.write(script)
            script_path = f.name

        try:
            result = subprocess.run(
                ['node', script_path],
                capture_output=True, text=True, timeout=120,
                cwd=impl_dir,
            )
            if result.returncode == 0:
                return json.loads(result.stdout.strip())
            else:
                return {"error": result.stderr[:500]}
        except Exception as e:
            return {"error": str(e)}
        finally:
            os.unlink(script_path)

    def _analyze_evidence_quality(self, graph: EvidenceGraph, glm_trace: dict) -> dict:
        """Analyze whether GLiREL evidence would help the GLM adjudicator.

        Questions (per CTO directive §17):
          1. Did GLiREL extract useful source-local relations?
          2. Did it extract useful cross-source relations?
          3. Did it expose evidence the GLM previously missed?
          4. Did it introduce false relations?
          5. Could the GLM adjudicator make a better decision with the structured graph?
        """
        glm_label = glm_trace.get("classification", {}).get("label", "UNKNOWN")
        glm_state = glm_trace.get("classification", {}).get("iss_state", "UNKNOWN")

        return {
            "question_1_useful_source_local": {
                "source_a_edges": len(graph.source_local_edges_a),
                "source_b_edges": len(graph.source_local_edges_b),
                "assessment": "yes" if (len(graph.source_local_edges_a) > 0 or len(graph.source_local_edges_b) > 0) else "no",
            },
            "question_2_useful_cross_source": {
                "has_a_and_b_evidence": graph.has_cross_source_evidence(),
                "assessment": "yes" if graph.has_cross_source_evidence() else "no",
            },
            "question_3_exposed_missed_evidence": {
                "glm_label": glm_label,
                "glm_state": glm_state,
                "glirel_relation_count": len(graph.edges),
                "assessment": "needs_manual_review",
            },
            "question_4_false_relations": {
                "assessment": "needs_manual_review",
                "note": "Requires human adjudication of GLiREL output quality",
            },
            "question_5_better_decision_possible": {
                "assessment": "needs_manual_review",
                "note": "Requires comparing hybrid vs frozen-only on same cases",
            },
        }
