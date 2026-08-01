"""
Patent Wedge Workflow

The primary product surface:
> Upload a patent and discover everything it could become.

This is the first product. Not all three businesses simultaneously.

Workflow:
    Patent / invention disclosure
    -> parse
    -> map to graph
    -> identify adjacent patents and inventions
    -> find cemetery analogues
    -> identify missing prerequisites
    -> generate permutations
    -> score candidates
    -> destroyer attack
    -> blueprint generation
    -> business report
    -> Discovery Delta scoring
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from product.ingestion.patent_parser import PatentParser
from product.retrieval.graph_retriever import GraphRetriever
from product.permutation.engine import PermutationEngine
from product.blueprint.composer import BlueprintComposer
from product.reporting.generator import ReportGenerator
from product.discovery.delta import DiscoveryDelta


class PatentWedge:
    """
    End-to-end patent-to-discovery pipeline.
    
    This is the primary commercial workflow.
    A user uploads a patent and discovers everything it could become.
    """

    def __init__(self, graph_path: Optional[str] = None):
        if graph_path is None:
            graph_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "data", "civilization_graph.json"
            )

        self.parser = PatentParser()
        self.retriever = GraphRetriever(graph_path)
        self.permutation = PermutationEngine()
        self.blueprint = BlueprintComposer()
        self.reporter = ReportGenerator()
        self.dd = DiscoveryDelta()

    def analyze(self, patent_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full patent-to-discovery workflow.
        
        Args:
            patent_input: Dict with patent text, claims, metadata
            
        Returns:
            Complete discovery report with DD score
        """
        start = time.time()
        assumptions = []
        warnings = []

        # Step 1: Parse
        assumptions.append("Patent text is complete and accurately represented")
        parsed = self.parser.parse(patent_input)

        # Step 2: Map to graph
        assumptions.append("Graph contains relevant domain nodes")
        graph_context = self.retriever.retrieve(parsed)

        # Step 3: Find cemetery analogues
        assumptions.append("Cemetery entries are relevant to this domain")
        cemetery_matches = self.retriever.cemetery_lookup(parsed)

        # Step 4: Generate permutations
        assumptions.append("Pairwise and triple combinations are meaningful")
        permutations = self.permutation.generate(parsed, graph_context)

        # Step 5: Score candidates
        assumptions.append("PCS, CIS, feasibility scores are calibrated")
        scored = self.permutation.score(permutations)

        # Step 6: Blueprint generation
        assumptions.append("Blueprint templates are applicable to this domain")
        blueprints = []
        for candidate in scored[:5]:  # Top 5 candidates
            bp = self.blueprint.compose(candidate, mode="business")
            blueprints.append(bp)

        # Step 7: Business report
        report = self.reporter.business_report(
            parsed=parsed,
            adjacencies=graph_context.get("adjacencies", []),
            permutations=scored,
            blueprints=blueprints,
            cemetery=cemetery_matches,
            warnings=warnings,
        )

        # Step 8: Discovery Delta
        pipeline_output = {
            "adjacency_map": graph_context.get("adjacencies", []),
            "candidates": scored,
            "permutations": permutations,
            "blueprints": blueprints,
            "cemetery_matches": cemetery_matches,
            "warnings": warnings,
            "risk_register": report.get("risk_register", []),
        }

        dd_result = self.dd.score(pipeline_output, patent_input)

        duration = time.time() - start

        return {
            "patent_id": patent_input.get("id", "unknown"),
            "title": patent_input.get("title", "Untitled"),
            "domain": parsed.get("domain", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(duration, 3),
            "assumptions": assumptions,
            "warnings": warnings,
            "discovery_delta": dd_result,
            "report": report,
            "blueprints": blueprints,
            "cemetery_matches": cemetery_matches,
            "permutation_count": len(permutations),
            "scored_candidate_count": len(scored),
        }

    def analyze_text(self, text: str, title: str = "Untitled") -> Dict[str, Any]:
        """Convenience method: analyze raw patent text."""
        return self.analyze({
            "id": f"adhoc_{int(time.time())}",
            "title": title,
            "text": text,
            "source": "user_input",
        })

    def analyze_file(self, path: str) -> Dict[str, Any]:
        """Convenience method: analyze a patent file (JSON or text)."""
        with open(path, "r") as f:
            if path.endswith(".json"):
                data = json.load(f)
            else:
                data = {
                    "id": os.path.basename(path).replace(".txt", ""),
                    "title": os.path.basename(path),
                    "text": f.read(),
                    "source": "file_upload",
                }
        return self.analyze(data)

    def batch_analyze(self, inputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze multiple patents and return aggregate DD."""
        results = []
        for inp in inputs:
            result = self.analyze(inp)
            results.append(result)

        return {
            "total": len(results),
            "results": results,
            "dd_summary": self.dd.summary(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def export_dd(self, path: str):
        """Export Discovery Delta history."""
        self.dd.export(path)
