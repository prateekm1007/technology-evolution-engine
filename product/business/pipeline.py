from product.ingestion.patent_parser import PatentParser
from product.retrieval.graph_retriever import GraphRetriever
from product.permutation.engine import PermutationEngine
from product.blueprint.composer import BlueprintComposer
from product.reporting.generator import ReportGenerator


class BusinessPipeline:
    """Top-level business report pipeline.

    Phase 1 (Amendment directive) — Silent failure elimination:

    Every stage must raise loudly on bad input or broken state. The old
    code returned empty/zero-valued results that looked like valid
    negative outputs. That made it impossible to distinguish:
        (a) a real negative result (the input had no extractable signal)
        (b) a broken call (the input schema was wrong, a stage crashed
            internally, or an upstream component returned malformed data)

    Per the Final Non-Negotiable Principle:
        "A low score from a valid measurement is more valuable than
         a high score from a circular measurement."

    A silent-failure pipeline produces neither — it produces an
    uninterpretable score. This is unacceptable for any downstream
    scientific use, including the upcoming discrimination study.

    Stage-level contracts (added in Phase 1):
        parser.run(d)       -> dict with non-empty 'patent_id', 'word_count' > 0
        retriever.run(p)    -> dict with 'total_nodes_searched' >= 0
        permuter.run({...}) -> dict with 'total_generated' >= 0
        blueprinter.run({...})-> dict with 'blueprints' list (may be empty)
        reporter.run({...}) -> dict with 'report_id', 'report_type'

    Each stage is allowed to return an empty result, but only when the
    input was valid. If the input was invalid (wrong schema, missing
    required field, internally inconsistent), the stage MUST raise.
    """

    # Stages whose results are required to be non-empty (when input is valid).
    # Empty result here means either invalid input or upstream silent failure.
    _STAGE_REQUIRED_KEYS = {
        'parser':     {'patent_id', 'word_count', 'components'},
        'retrieval':  {'matched_nodes', 'adjacency_map', 'cemetery_matches',
                       'prerequisite_gaps', 'total_nodes_searched',
                       'total_edges_searched'},
        'permutation':{'total_generated', 'total_scored', 'candidates'},
        'blueprint':  {'blueprints', 'total_viable', 'mode'},
        'report':     {'report_id', 'report_type', 'epistemic_status'},
    }

    def __init__(self, graph_path=None):
        self.parser = PatentParser()
        self.retriever = GraphRetriever(graph_path=graph_path)
        self.permuter = PermutationEngine(max_permutations=50)
        self.blueprinter = BlueprintComposer()
        self.reporter = ReportGenerator()

    def run(self, d):
        # Per DR-62 (cycle 198): input validation — raise loudly on unexpected schema.
        # The old code silently returned empty results when given {'text': ...} instead
        # of {'raw_text': ...}, producing a zero-valued report that looked like a valid
        # negative result instead of a broken call.
        if not isinstance(d, dict):
            raise ValueError(
                f"BusinessPipeline.run() expects a dict, got {type(d).__name__}"
            )
        if 'raw_text' not in d:
            raise ValueError(
                f"BusinessPipeline.run() requires 'raw_text' key. "
                f"Got keys: {list(d.keys())}. "
                f"This is DR-62: the old code silently returned empty results "
                f"on malformed input — now it raises loudly."
            )
        # Phase 1: also reject empty raw_text — an empty input produces
        # an empty parser output that silently flows through every stage
        # and produces a zero-valued report indistinguishable from a
        # real negative. This is the silent-failure pattern that the
        # Amendment directive targets.
        raw_text = d.get('raw_text', '')
        if not isinstance(raw_text, str) or not raw_text.strip():
            raise ValueError(
                f"BusinessPipeline.run() requires non-empty string 'raw_text'. "
                f"Got type={type(raw_text).__name__}, "
                f"value_repr={repr(raw_text)[:100]}. "
                f"Empty input would flow through every stage silently "
                f"and produce a zero-valued report indistinguishable from "
                f"a real negative result (Phase 1 silent-failure fix)."
            )

        # ===== STAGE 1: Parser =====
        # PatentParser.run() uses .get('raw_text','') — if the key is missing
        # it returns empty data. We have already validated raw_text above,
        # but we add a stage-output contract check to catch any future
        # silent failure inside the parser.
        parsed = self.parser.run(d)
        self._check_stage_output('parser', parsed)

        # Phase 1: an empty parse (no components AND no materials AND no
        # claims AND word_count < 10) is suspicious. Either the input is
        # too short to be a meaningful patent, or the parser silently
        # failed to extract anything. We raise rather than emit a
        # zero-valued report.
        if (not parsed.get('components') and
            not parsed.get('materials') and
            not parsed.get('claims') and
            parsed.get('word_count', 0) < 10):
            raise ValueError(
                f"Parser returned empty extraction (no components, materials, "
                f"or claims; word_count={parsed.get('word_count', 0)}). "
                f"This is either a too-short input or a parser silent failure. "
                f"Refusing to produce a zero-valued report (Phase 1 fix)."
            )

        # ===== STAGE 2: Retriever =====
        # GraphRetriever.run() can silently return zero matches if the graph
        # failed to load (the property catches Exception and returns empty).
        # We check the stage output contract and warn loudly if the graph
        # appears to have failed to load.
        retrieval = self.retriever.run(parsed)
        self._check_stage_output('retrieval', retrieval)

        # Phase 1: if total_nodes_searched is 0, the graph failed to load
        # (or is genuinely empty). This is a silent-failure signature.
        # We raise so the operator knows the graph is missing.
        if retrieval.get('total_nodes_searched', 0) == 0:
            raise RuntimeError(
                f"Retriever searched 0 graph nodes. Either the graph file "
                f"is missing/corrupt, or it is genuinely empty. "
                f"graph_path={self.retriever.graph_path}. "
                f"Refusing to produce a report based on an empty graph "
                f"(Phase 1 silent-failure fix)."
            )

        # ===== STAGE 3: Permuter =====
        # PermutationEngine.run() silently returns total_generated=0 if no
        # elements were extracted. We have already validated parser output
        # above, so 0 here means a silent permuter bug.
        permutation = self.permuter.run({'parsed': parsed, 'retrieval': retrieval})
        self._check_stage_output('permutation', permutation)

        if permutation.get('total_generated', 0) == 0:
            raise RuntimeError(
                f"Permuter generated 0 candidates despite non-empty parser "
                f"output (components={len(parsed.get('components', []))}, "
                f"materials={len(parsed.get('materials', []))}, "
                f"methods={len(parsed.get('methods', []))}). "
                f"This is a silent permuter failure (Phase 1 fix)."
            )

        # ===== STAGE 4: Blueprint Composer =====
        # BlueprintComposer.run() may legitimately return 0 blueprints if no
        # candidate scores above 0.3. That is a real negative. We do NOT
        # raise here — empty blueprints is a valid result, not a silent
        # failure.
        blueprint = self.blueprinter.run({
            'candidates': permutation.get('candidates', []),
            'mode': 'business',
            'max_blueprints': 5,
        })
        self._check_stage_output('blueprint', blueprint)

        # ===== STAGE 5: Report Generator =====
        report = self.reporter.run({
            'mode': 'business',
            'parsed': parsed,
            'retrieval': retrieval,
            'permutation': permutation,
            'blueprint': blueprint,
        })
        self._check_stage_output('report', report)

        return report

    def _check_stage_output(self, stage_name, output):
        """Verify the stage produced a structurally valid output.

        Raises TypeError if output is not a dict.
        Raises KeyError if a required key is missing.

        This catches silent failures where a stage returns None or a
        malformed dict that would otherwise flow downstream and produce
        a zero-valued report.
        """
        if not isinstance(output, dict):
            raise TypeError(
                f"Stage '{stage_name}' returned {type(output).__name__}, "
                f"expected dict. This is a silent-failure signature: "
                f"the stage crashed internally and returned None or a "
                f"non-dict. Refusing to propagate (Phase 1 fix)."
            )
        required = self._STAGE_REQUIRED_KEYS.get(stage_name, set())
        missing = [k for k in required if k not in output]
        if missing:
            raise KeyError(
                f"Stage '{stage_name}' output missing required keys: "
                f"{missing}. Got keys: {list(output.keys())}. "
                f"This is a silent-failure signature: the stage produced "
                f"a partial result that would flow downstream as a "
                f"zero-valued report. Refusing to propagate (Phase 1 fix)."
            )
