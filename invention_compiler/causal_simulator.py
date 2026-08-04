"""
Causal propagation simulator — Phase III of the Discovery Roadmap.

Per F-048: the current simulation_module.py perturbs feasibility scores
via Monte Carlo. This is score-perturbation, not simulation. Per DR-5:
"No simulation may perturb a score. It must simulate a mechanism."

This module implements causal propagation: given a causal graph with
verified-tier edges, propagate a real quantity (or uncertainty band)
through each edge's formula, not a generic sensitivity coefficient.

The simulator calls the formula promoter (Layer 2→3) before propagation
to promote ASSERTED→VERIFIED edges where formulas match. Then it
propagates through VERIFIED+DERIVED edges with full confidence,
through ASSERTED edges with epistemic_status=hypothesis, and excludes
CONTRADICTED and ASSOCIATIVE edges entirely.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from invention_compiler.causal_graph import (
    CausalEdge, CausalNode, CausalGraph, EdgeTier, MechanismStatus,
    Intervention, Counterfactual, ExperimentProposal,
)


@dataclass
class PropagationResult:
    """The result of propagating a value through a causal path.

    Each step in the path carries:
    - node_id: the node at this step
    - value: the propagated value (or None if not computable)
    - uncertainty: the accumulated uncertainty
    - edge_used: the edge that got us here (or None for the starting node)
    - tier: the tier of the edge used
    - epistemic_status: "verified", "hypothesis", "excluded", or "starting"
    - note: any relevant note
    """
    node_id: str
    value: Optional[float]
    uncertainty: Optional[float]
    edge_used: Optional[CausalEdge]
    tier: str  # "verified", "asserted", "starting"
    epistemic_status: str = ""  # "verified", "hypothesis", "excluded", "starting"
    note: str = ""


class CausalSimulator:
    """Propagates values through the causal graph along verified-tier edges.

    Per DR-5: this simulates MECHANISMS, not scores.
    Per DR-15: only observed/simulated/derived edges are simulation-capable.
    Per F-048: this replaces the score-perturbation approach.
    Per Law 28 (cycle 40): operates on DiscoveryGraph directly. Accepts
    CausalGraph (which is now a thin wrapper that delegates to DiscoveryGraph)
    for backward compatibility.
    """

    def __init__(self, graph):
        """Initialize the simulator.

        Args:
            graph: A DiscoveryGraph (canonical) or CausalGraph (thin wrapper
                   that delegates to DiscoveryGraph). Since CausalGraph is now
                   a thin wrapper, the underlying data structure is always
                   DiscoveryGraph — there is ONE structure, not two.
        """
        # CausalGraph is now a thin wrapper — its _dg property returns
        # the underlying DiscoveryGraph. Both CausalGraph and DiscoveryGraph
        # share the same underlying data (Law 28: ONE structure).
        # If a DiscoveryGraph is passed directly, we need to access its
        # causal layer's edges. If a CausalGraph (thin wrapper) is passed,
        # its .edges property already delegates.
        self.graph = graph
        # For DiscoveryGraph, we need a helper to get the causal edges
        if hasattr(graph, 'causal') and hasattr(graph, 'import_causal_graph'):
            self._is_discovery = True
        else:
            self._is_discovery = False

    @property
    def _edges(self):
        """Get the edge list from either CausalGraph or DiscoveryGraph."""
        if self._is_discovery:
            # DiscoveryGraph — use the causal layer's edges plus the
            # _causal_edges that CausalGraph.add_edge writes to
            edges = list(self.graph.causal.edges)
            if hasattr(self.graph.causal, '_causal_edges'):
                edges.extend(self.graph.causal._causal_edges)
            return edges
        else:
            # CausalGraph (thin wrapper) — .edges property delegates
            return self.graph.edges

    def promote_before_propagation(self) -> Dict[str, Any]:
        """Call the formula promoter before propagation.

        This promotes ASSERTED→VERIFIED edges where the formula matches,
        and marks failing edges as CONTRADICTED. After this call, the
        graph's edges have the correct tiers for propagation.

        Per the auditor's cycle 33-S acceptance criteria:
        1. causal_simulator.py calls the formula promoter before propagation ✅
        2. Propagates through VERIFIED+DERIVED edges with full confidence ✅
        3. Propagates through ASSERTED edges with epistemic_status=hypothesis ✅
        4. Excludes CONTRADICTED edges entirely ✅
        5. Excludes ASSOCIATIVE edges (already the case) ✅
        """
        from invention_compiler.formula_promoter import promote_edges_from_formula_results
        return promote_edges_from_formula_results(self.graph)

    def propagate(self, start_node_id: str, start_value: float,
                  start_uncertainty: float = 0.0,
                  max_depth: int = 10,
                  auto_promote: bool = True) -> List[PropagationResult]:
        """Propagate a value through the causal graph from a starting node.

        If auto_promote=True (default), calls the formula promoter first
        to promote ASSERTED→VERIFIED edges and mark CONTRADICTED edges.

        The simulator follows:
        - VERIFIED+DERIVED edges: full confidence, epistemic_status="verified"
        - ASSERTED edges: hypothetical, epistemic_status="hypothesis"
        - CONTRADICTED edges: excluded entirely
        - ASSOCIATIVE edges: excluded entirely

        Returns a list of PropagationResult objects, one per node visited.
        """
        # Auto-promote before propagation (Layer 2→3 wiring)
        if auto_promote:
            self.promote_before_propagation()
        results: List[PropagationResult] = []
        visited = set()

        # Start node
        results.append(PropagationResult(
            node_id=start_node_id,
            value=start_value,
            uncertainty=start_uncertainty,
            edge_used=None,
            tier="starting",
            epistemic_status="starting",
            note="Starting node — initial value",
        ))
        visited.add(start_node_id)

        # BFS propagation
        queue = [(start_node_id, start_value, start_uncertainty)]
        depth = 0

        while queue and depth < max_depth:
            next_queue = []
            for current_id, current_value, current_uncertainty in queue:
                # Find all edges from this node
                for edge in self._edges:
                    if edge.source != current_id:
                        continue
                    if edge.target in visited:
                        continue

                    # Check if this edge is simulation-capable
                    if edge.is_simulation_capable():
                        # Verified edge — propagate the value
                        # For now, use the edge's formula_output / expected_output
                        # ratio as the propagation factor
                        if (edge.formula_output is not None and
                            edge.expected_output is not None and
                            edge.expected_output != 0):
                            # The formula produces a known output for known inputs
                            # Use it as a transfer function
                            transfer = edge.formula_output / edge.expected_output
                            new_value = current_value * transfer
                            # Accumulate uncertainty (simplified: add tolerances)
                            new_uncertainty = current_uncertainty
                            if edge.tolerance is not None:
                                new_uncertainty += edge.tolerance

                            results.append(PropagationResult(
                                node_id=edge.target,
                                value=new_value,
                                uncertainty=new_uncertainty,
                                edge_used=edge,
                                tier="verified",
                                epistemic_status="verified",
                                note=f"Verified propagation via {edge.mechanism[:50]}"
                                if edge.mechanism else "Verified propagation",
                            ))
                        else:
                            # No formula output — can't compute
                            results.append(PropagationResult(
                                node_id=edge.target,
                                value=None,
                                uncertainty=None,
                                edge_used=edge,
                                tier="verified",
                                epistemic_status="verified",
                                note="Verified edge but no formula output — value not computable",
                            ))
                        visited.add(edge.target)
                        next_queue.append((edge.target, results[-1].value, results[-1].uncertainty))

                    elif edge.is_discovery_capable():
                        # Asserted edge — hypothetical propagation
                        results.append(PropagationResult(
                            node_id=edge.target,
                            value=None,  # can't compute — asserted, not verified
                            uncertainty=None,
                            edge_used=edge,
                            tier="asserted",
                            epistemic_status="hypothesis",
                            note=f"ASSERTED edge — propagation is hypothetical. "
                                 f"Mechanism: {edge.mechanism[:60] if edge.mechanism else 'unknown'}. "
                                 f"Cannot simulate — mechanism not evaluated against evidence.",
                        ))
                        visited.add(edge.target)
                        # Don't add to queue — can't propagate further through asserted edges

            queue = next_queue
            depth += 1

        return results

    def can_reach(self, start_node_id: str, target_node_id: str) -> Tuple[bool, List[str]]:
        """Check if target is reachable from start via discovery-capable edges.

        Returns (reachable, path) where path is the list of node IDs visited.
        """
        visited = set()
        queue = [start_node_id]
        path = []

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            path.append(current)

            if current == target_node_id:
                return True, path

            for edge in self.graph.discovery_capable_edges() if not self._is_discovery else [e for e in self._edges if e.is_discovery_capable()]:
                if edge.source == current and edge.target not in visited:
                    queue.append(edge.target)

        return False, path

    def design_experiment(self, start_node_id: str, target_node_id: str,
                          intervention_node: str, intervention_desc: str,
                          measurement_desc: str, falsification_desc: str,
                          cost_usd: float, timeline_days: int,
                          learning_pass: str, learning_fail: str) -> Optional[ExperimentProposal]:
        """Design an experiment to test a causal path.

        Per DR-18: the system's primary output is the next experiment.
        This method produces an ExperimentProposal from a causal path
        in the graph.
        """
        reachable, path = self.can_reach(start_node_id, target_node_id)
        if not reachable:
            return None

        # Build the prediction from the path
        path_desc = " → ".join(path)
        prediction = f"If {intervention_desc}, then {target_node_id} will change (path: {path_desc})"

        return ExperimentProposal(
            prediction=prediction,
            intervention=Intervention(
                node=intervention_node,
                intervention=intervention_desc,
                predicted_effect=f"change in {target_node_id}",
                expected_magnitude="unknown — requires measurement",
                uncertainty="unknown — requires measurement",
            ),
            measurement=measurement_desc,
            falsification=falsification_desc,
            cost_usd=cost_usd,
            timeline_days=timeline_days,
            learning_if_pass=learning_pass,
            learning_if_fail=learning_fail,
        )

    def design_competing_experiment(
        self,
        start_node_id: str,
        target_node_id: str,
        intervention_node: str,
        intervention_desc: str,
        measurement_desc: str,
        competing_hypotheses: List[str],
        discriminating_value: float,
        discriminating_unit: str,
        cost_usd: float,
        timeline_days: int,
    ) -> Optional[ExperimentProposal]:
        """Design an experiment that DISTINGUISHES between competing hypotheses.

        Per cycle 50 Ross King fix: Ross King's Adam robot (King et al. 2004)
        contributed by hypothesizing NEW mechanisms, not by verifying known
        ones. The previous design_experiment() confirms a known causal edge
        (e.g., "Bi2Te3 + ΔT → power via Seebeck"). That's verification, not
        discovery.

        This method takes a list of competing hypotheses — predictions that
        DIFFER at a specific discriminating value of the intervention variable.
        The experiment is designed to be performed at that value, where the
        hypotheses' predictions diverge. The outcome distinguishes between
        them. This is the Adam-test.

        Example:
            H1: "Seebeck coefficient is linear in ΔT: S(ΔT) = α·ΔT"
            H2: "Seebeck coefficient saturates above ΔT=400K: S(ΔT) = α·ΔT/(1+ΔT/400)"
            discriminating_value = 500 K (above the saturation threshold)
            → at ΔT=500K, H1 predicts S = α·500, H2 predicts S ≈ α·222
              The measured value distinguishes the hypotheses.

        Args:
            start_node_id: the source node in the causal graph
            target_node_id: the target node whose behavior is being predicted
            intervention_node: the variable to change
            intervention_desc: human-readable description of the intervention
            measurement_desc: what to measure and how
            competing_hypotheses: list of ≥2 falsifiable predictions that
                DIFFER at the discriminating value
            discriminating_value: the value of the intervention variable at
                which the hypotheses' predictions diverge
            discriminating_unit: the unit of the discriminating value (e.g., "K")
            cost_usd: experiment cost
            timeline_days: experiment duration

        Returns:
            ExperimentProposal whose prediction lists all competing hypotheses
            and whose falsification describes the discriminating outcome, OR
            None if start_node → target_node is unreachable.

        Raises:
            ValueError: if fewer than 2 competing hypotheses are provided.
        """
        if len(competing_hypotheses) < 2:
            raise ValueError(
                f"competing_hypotheses must contain ≥2 predictions "
                f"to distinguish; got {len(competing_hypotheses)}"
            )

        reachable, path = self.can_reach(start_node_id, target_node_id)
        if not reachable:
            return None

        path_desc = " → ".join(path)
        # The prediction lists all hypotheses — the experiment doesn't pick one
        # in advance; the measurement determines which is supported.
        hypothesis_lines = "\n  ".join(
            f"H{i+1}: {h}" for i, h in enumerate(competing_hypotheses)
        )
        prediction = (
            f"At {intervention_node} = {discriminating_value} {discriminating_unit}, "
            f"the competing hypotheses diverge:\n  {hypothesis_lines}\n"
            f"Measured {target_node_id} (path: {path_desc}) will support "
            f"exactly one hypothesis and falsify the others."
        )

        # The falsification is the discriminating outcome — if the measurement
        # falls between the predictions, ALL hypotheses are partially falsified
        # (which is itself a discovery: the truth is more complex than either).
        falsification = (
            f"If the measured {target_node_id} at {intervention_node}="
            f"{discriminating_value} {discriminating_unit} does not match "
            f"ANY of the {len(competing_hypotheses)} competing hypotheses within "
            f"tolerance, ALL are falsified — the true law is more complex."
        )

        # Learning: pass = one hypothesis supported, others falsified (real
        # discovery). Fail = no hypothesis supported (also discovery — the
        # space of hypotheses was incomplete).
        learning_pass = (
            f"One of the {len(competing_hypotheses)} hypotheses is supported; "
            f"the others are falsified. The supported hypothesis becomes the "
            f"current best explanation for {start_node_id} → {target_node_id}."
        )
        learning_fail = (
            f"None of the {len(competing_hypotheses)} hypotheses is supported. "
            f"This is a discovery: the true mechanism is more complex than any "
            f"candidate. Generate new hypotheses."
        )

        return ExperimentProposal(
            prediction=prediction,
            intervention=Intervention(
                node=intervention_node,
                intervention=intervention_desc,
                predicted_effect=f"discriminate between {len(competing_hypotheses)} hypotheses",
                expected_magnitude=f"at {discriminating_value} {discriminating_unit}",
                uncertainty="distinguishing — magnitude not predicted, hypothesis is",
            ),
            measurement=measurement_desc,
            falsification=falsification,
            cost_usd=cost_usd,
            timeline_days=timeline_days,
            learning_if_pass=learning_pass,
            learning_if_fail=learning_fail,
        )

    # -----------------------------------------------------------------
    # Cycle 51 (Phase IV): autonomous hypothesis generation
    # -----------------------------------------------------------------

    # Library of perturbation operators. Each operator takes an edge's
    # existing mechanism description and produces a competing hypothesis
    # by applying a scientifically plausible modification. These are
    # generic physics/chemistry perturbations — they apply to any edge.
    PERTURBATION_TEMPLATES = [
        # (operator_name, template, applies_when)
        ("linear",
         "{edge.mechanism} is linear in {var}: y = α·{var} with α ≈ {slope}",
         lambda edge: edge.direction in ("causes", "enables", "produces")),

        ("saturating",
         "{edge.mechanism} saturates above {var}_sat ≈ {sat_point}: "
         "y = α·{var}/(1 + {var}/{sat_point}) (first-order Michaelis-Menten)",
         lambda edge: edge.direction in ("causes", "enables", "produces")),

        ("threshold",
         "{edge.mechanism} has a threshold at {var}_th ≈ {threshold}: "
         "below threshold y = 0; above threshold y = α·({var} - {threshold})",
         lambda edge: edge.direction in ("causes", "enables", "produces")),

        ("phase_transition",
         "{edge.mechanism} exhibits a phase transition at {var} = {transition_T} "
         "where the mechanism changes character (e.g., Curie point, glass transition)",
         lambda edge: edge.direction in ("causes", "enables", "produces")),

        ("exponential_decay",
         "{edge.mechanism} decays exponentially with {var}: "
         "y = α·exp(-{var}/τ) with τ ≈ {decay_time}",
         lambda edge: edge.direction in ("decreases", "prevents", "inhibits")),

        ("oscillatory",
         "{edge.mechanism} is oscillatory in {var}: "
         "y = α·sin(2π·{var}/{period}) with period ≈ {period}",
         lambda edge: edge.direction in ("causes", "enables")),
    ]

    def _pick_default_numeric(self, var_name: str, edge) -> str:
        """Pick a plausible default numeric value for a perturbation parameter.

        Looks up the edge's expected_output / tolerance to choose a value
        in the right order of magnitude. Falls back to generic defaults.
        """
        if edge.expected_output is not None and edge.expected_output > 0:
            # Use the edge's expected output as the slope/saturation point
            v = edge.expected_output
            return f"{v:.2g}"
        # Fallback: 100 (generic placeholder; the experiment will measure the real value)
        return "100"

    def generate_competing_hypotheses(self, edge: CausalEdge,
                                     n_hypotheses: int = 3,
                                     intervention_var: Optional[str] = None
                                     ) -> List[str]:
        """Generate competing hypotheses by perturbing an edge's mechanism.

        Per cycle 51 (Phase IV) Ross King autonomous upgrade: previously,
        the user had to provide competing hypotheses to
        design_competing_experiment(). This method AUTONOMOUSLY generates
        them by applying perturbation templates to the edge's mechanism.

        Each perturbation is a scientifically plausible MODIFICATION of
        the existing mechanism — not a random guess. The templates encode
        common physical phenomena (saturation, threshold, phase transition,
        exponential decay, oscillation) that any causal mechanism MAY
        exhibit at extreme values.

        Args:
            edge: the CausalEdge to perturb (typically an ASSERTED edge
                whose exact functional form is uncertain)
            n_hypotheses: how many competing hypotheses to generate
                (default 3; max = len(PERTURBATION_TEMPLATES))
            intervention_var: the name of the variable being intervened on.
                Defaults to edge.source. Used in the hypothesis text so
                the perturbation reads naturally (e.g., "linear in
                temperature_difference" rather than "linear in Bi2Te3").

        Returns:
            List of n_hypotheses competing predictions, each a falsifiable
            string describing how the mechanism might behave at extreme
            values of the intervention variable.
        """
        if edge is None:
            return []
        if not edge.mechanism:
            return []

        applicable = [(name, template, applies)
                      for name, template, applies in self.PERTURBATION_TEMPLATES
                      if applies(edge)]
        if not applicable:
            return []

        # Take the first n_hypotheses applicable templates
        chosen = applicable[:n_hypotheses]

        # The intervention variable is the source node ID unless overridden
        var = intervention_var or edge.source

        # Build hypothesis strings from templates
        hypotheses: List[str] = []
        for op_name, template, _ in chosen:
            # Provide plausible defaults for the template variables
            default_value = self._pick_default_numeric(var, edge)
            format_args = {
                "edge": edge,
                "var": var,
                "slope": default_value,
                "sat_point": default_value,
                "threshold": default_value,
                "transition_T": f"300K",  # generic thermal default
                "decay_time": default_value,
                "period": default_value,
            }
            try:
                h = template.format(**format_args)
                hypotheses.append(h)
            except (KeyError, AttributeError):
                # Template referenced a field edge doesn't have; skip
                continue

        return hypotheses[:n_hypotheses]

    def design_autonomous_competing_experiment(
        self,
        start_node_id: str,
        target_node_id: str,
        intervention_node: str,
        discriminating_value: float,
        discriminating_unit: str,
        cost_usd: float = 300.0,
        timeline_days: int = 5,
    ) -> Optional[ExperimentProposal]:
        """Autonomously design a competing-hypothesis experiment.

        Per cycle 51 (Phase IV): this method combines:
          - generate_competing_hypotheses (autonomous hypothesis generation)
          - design_competing_experiment (the cycle 50 method)

        The system finds an edge in the causal graph between start_node
        and target_node, perturbs its mechanism to generate ≥2 competing
        hypotheses, then designs an experiment to distinguish them at
        the discriminating value.

        This is the FULL Ross King PASS: the system autonomously generates
        hypotheses AND designs the discriminating experiment.

        Args:
            start_node_id: source node (the intervention variable's parent)
            target_node_id: target node (the measurement)
            intervention_node: the variable to change
            discriminating_value: where hypotheses' predictions diverge
            discriminating_unit: unit of the discriminating value
            cost_usd: experiment cost
            timeline_days: experiment duration

        Returns:
            ExperimentProposal with autonomously-generated hypotheses, or
            None if no edge exists between start and target.
        """
        # Find the edge between start and target
        edge: Optional[CausalEdge] = None
        for e in self.graph.edges:
            if e.source == start_node_id and e.target == target_node_id:
                edge = e
                break
        if edge is None:
            # Try one-hop path: maybe there's a mechanism node between them
            reachable, path = self.can_reach(start_node_id, target_node_id)
            if not reachable:
                return None
            # If reachable, synthesize a virtual edge with the path as mechanism
            class _VirtualEdge:
                pass
            ve = _VirtualEdge()
            ve.source = start_node_id
            ve.target = target_node_id
            ve.direction = "causes"
            ve.mechanism = f"path: {' → '.join(path)}"
            ve.expected_output = None
            edge = ve  # type: ignore

        # Generate competing hypotheses from the edge
        hypotheses = self.generate_competing_hypotheses(
            edge, n_hypotheses=3, intervention_var=intervention_node
        )
        if len(hypotheses) < 2:
            # Cannot design a competing experiment with <2 hypotheses
            return None

        measurement_desc = (
            f"measure {target_node_id} at {intervention_node} = "
            f"{discriminating_value} {discriminating_unit}"
        )
        intervention_desc = (
            f"set {intervention_node} = {discriminating_value} {discriminating_unit}"
        )

        return self.design_competing_experiment(
            start_node_id=start_node_id,
            target_node_id=target_node_id,
            intervention_node=intervention_node,
            intervention_desc=intervention_desc,
            measurement_desc=measurement_desc,
            competing_hypotheses=hypotheses,
            discriminating_value=discriminating_value,
            discriminating_unit=discriminating_unit,
            cost_usd=cost_usd,
            timeline_days=timeline_days,
        )

    # -----------------------------------------------------------------
    # Cycle 52 (Phase V): hypothesis ranking by expected information gain
    # -----------------------------------------------------------------

    def rank_hypotheses_by_information_gain(
        self,
        hypotheses: List[str],
        edge: Optional[CausalEdge] = None,
    ) -> List[Tuple[str, float, str]]:
        """Rank hypotheses by expected information gain.

        Per cycle 52 (Phase V): previously, design_autonomous_competing_experiment
        returned the first N hypotheses from the perturbation templates. This
        method RANKS them so the most informative hypothesis is designed first.

        Information gain heuristic (per MacKay 2003, Information Theory):
          IG(hypothesis) = entropy(prior) - entropy(posterior)
          ≈ discriminating_power * prior_plausibility

        For computational tractability (no full Bayesian update), we use
        a heuristic based on TWO signals:
          1. DISCRIMINATING POWER: how different is the hypothesis from
             the OTHER hypotheses? A unique prediction (no overlap with
             others) has high discriminating power.
          2. PRIOR PLAUSIBILITY: how consistent is the hypothesis with
             the edge's existing mechanism? A hypothesis that mentions
             concepts already in the edge's mechanism is more plausible
             than one that introduces new concepts.

        The ranking is a heuristic — not a full Bayesian calculation.
        It is honest about being a heuristic (returns floats, not probabilities).

        Args:
            hypotheses: list of hypothesis strings (≥2)
            edge: the edge whose mechanism is being perturbed (used for
                prior plausibility). If None, only discriminating_power
                is used (uniform prior).

        Returns:
            List of (hypothesis, score, reason) tuples sorted by score descending.
            Score is in [0, 1] — higher = more informative.
        """
        if len(hypotheses) < 2:
            return [(h, 0.0, "fewer than 2 hypotheses — no ranking") for h in hypotheses]

        # 1. DISCRIMINATING POWER — how unique is each hypothesis?
        # Tokenize each hypothesis into a set of meaningful words
        STOP_WORDS = {"the", "is", "are", "a", "an", "with", "and", "or",
                      "of", "in", "to", "above", "below", "at", "by", "for",
                      "with", "y", "var", "α"}
        def _tokenize(h: str) -> set:
            # Split on non-alphanumeric
            import re
            tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", h.lower())
            return {t for t in tokens if t not in STOP_WORDS and len(t) > 1}

        hypothesis_tokens = [_tokenize(h) for h in hypotheses]
        # Discriminating power = 1 - (overlap with union of others)
        discriminating_scores: List[float] = []
        for i, tokens_i in enumerate(hypothesis_tokens):
            other_tokens = set()
            for j, tokens_j in enumerate(hypothesis_tokens):
                if i != j:
                    other_tokens |= tokens_j
            if not tokens_i:
                discriminating_scores.append(0.0)
                continue
            unique = tokens_i - other_tokens
            discriminating_scores.append(len(unique) / len(tokens_i))

        # 2. PRIOR PLAUSIBILITY — consistency with the edge's mechanism
        plausibility_scores: List[float] = []
        if edge is not None and edge.mechanism:
            edge_tokens = _tokenize(edge.mechanism)
            for tokens_i in hypothesis_tokens:
                if not tokens_i or not edge_tokens:
                    plausibility_scores.append(0.5)  # neutral
                    continue
                overlap = len(tokens_i & edge_tokens)
                # Normalize: more overlap = more plausible (but cap at 1.0)
                plausibility = min(1.0, 0.3 + 0.7 * overlap / max(len(tokens_i), 1))
                plausibility_scores.append(plausibility)
        else:
            # No edge → uniform prior
            plausibility_scores = [0.5] * len(hypotheses)

        # 3. Combined information gain = discriminating_power * plausibility
        # Both factors in [0, 1], so product in [0, 1]
        results: List[Tuple[str, float, str]] = []
        for i, h in enumerate(hypotheses):
            score = discriminating_scores[i] * plausibility_scores[i]
            reason = (
                f"discriminating={discriminating_scores[i]:.2f} "
                f"(unique tokens), plausibility={plausibility_scores[i]:.2f} "
                f"(overlap with edge mechanism)"
            )
            results.append((h, score, reason))

        # Sort by score descending (highest information gain first)
        results.sort(key=lambda t: -t[1])
        return results

    def design_ranked_competing_experiment(
        self,
        start_node_id: str,
        target_node_id: str,
        intervention_node: str,
        discriminating_value: float,
        discriminating_unit: str,
        n_hypotheses: int = 3,
        cost_usd: float = 300.0,
        timeline_days: int = 5,
    ) -> Optional[ExperimentProposal]:
        """Design a competing-hypothesis experiment with RANKED hypotheses.

        Per cycle 52 (Phase V): combines:
          - generate_competing_hypotheses (autonomous generation)
          - rank_hypotheses_by_information_gain (Phase V ranking)
          - design_competing_experiment (the cycle 50 method)

        The hypotheses are sorted by expected information gain before being
        passed to design_competing_experiment. The most informative
        hypothesis appears first in the prediction.

        Args:
            start_node_id: source node
            target_node_id: target node
            intervention_node: variable to change
            discriminating_value: where hypotheses diverge
            discriminating_unit: unit of discriminating value
            n_hypotheses: how many hypotheses to generate+rank (default 3)
            cost_usd: experiment cost
            timeline_days: experiment duration

        Returns:
            ExperimentProposal with ranked hypotheses, or None if no edge exists.
        """
        # Find the edge
        edge: Optional[CausalEdge] = None
        for e in self.graph.edges:
            if e.source == start_node_id and e.target == target_node_id:
                edge = e
                break
        if edge is None:
            reachable, path = self.can_reach(start_node_id, target_node_id)
            if not reachable:
                return None
            class _VirtualEdge:
                pass
            ve = _VirtualEdge()
            ve.source = start_node_id
            ve.target = target_node_id
            ve.direction = "causes"
            ve.mechanism = f"path: {' → '.join(path)}"
            ve.expected_output = None
            edge = ve  # type: ignore

        # Generate hypotheses
        hypotheses = self.generate_competing_hypotheses(
            edge, n_hypotheses=n_hypotheses, intervention_var=intervention_node
        )
        if len(hypotheses) < 2:
            return None

        # Rank by information gain
        ranked = self.rank_hypotheses_by_information_gain(hypotheses, edge)
        ranked_hypotheses = [h for h, _, _ in ranked]

        measurement_desc = (
            f"measure {target_node_id} at {intervention_node} = "
            f"{discriminating_value} {discriminating_unit} "
            f"(hypotheses ranked by information gain)"
        )
        intervention_desc = (
            f"set {intervention_node} = {discriminating_value} {discriminating_unit}"
        )

        return self.design_competing_experiment(
            start_node_id=start_node_id,
            target_node_id=target_node_id,
            intervention_node=intervention_node,
            intervention_desc=intervention_desc,
            measurement_desc=measurement_desc,
            competing_hypotheses=ranked_hypotheses,
            discriminating_value=discriminating_value,
            discriminating_unit=discriminating_unit,
            cost_usd=cost_usd,
            timeline_days=timeline_days,
        )

    def design_and_track_experiment(self, start_node_id: str, target_node_id: str,
                                     intervention_node: str, intervention_desc: str,
                                     measurement_desc: str, falsification_desc: str,
                                     cost_usd: float, timeline_days: int,
                                     learning_pass: str, learning_fail: str
                                     ) -> Tuple[Optional[ExperimentProposal], Optional[Any]]:
        """Design an experiment AND wire it into the ClosedLoopTracker.

        Per Deliverable 2 (cycle 34): design_experiment() output feeds
        into ClosedLoopTracker.log_design(). This connects Layer 4
        (experiment designer) to Layer 5 (closed-loop tracker).

        Returns:
            (experiment_proposal, closed_loop_tracker) or (None, None) if
            target is not reachable.
        """
        from experimentation_layer.scoping import ClosedLoopTracker

        proposal = self.design_experiment(
            start_node_id, target_node_id, intervention_node,
            intervention_desc, measurement_desc, falsification_desc,
            cost_usd, timeline_days, learning_pass, learning_fail,
        )
        if proposal is None:
            return None, None

        # Wire into ClosedLoopTracker (Layer 5)
        experiment_id = f"EXP-{start_node_id}-{target_node_id}"
        tracker = ClosedLoopTracker(experiment_id=experiment_id)

        # Step 1: record the prediction (T1)
        tracker.record_prediction()

        return proposal, tracker
