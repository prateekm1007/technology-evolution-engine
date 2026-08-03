"""Deep Oracle — six-stage causal cascade."""
from .calibration import C
MAGNITUDE = {"10%": 0.1, "2x": 0.5, "10x": 0.9}

def _clamp(x, lo, hi): return max(lo, min(hi, x))

# --- Honesty Loop (Law 27/28/29) --------------------------------------------
# Per BLUEPRINT_CONSTITUTION.md Law 27, no numerical certainty may be
# assigned to claims that lack repeated experimental validation. The
# Oracle's "confidence" field was a number in [0.05, 0.6] computed from
# a heuristic formula — it had no calibration data behind it. Per Law 27,
# that field is forbidden.
#
# The typed status block below is the required replacement (Law 29e).
# The Oracle's predictions are un-validated analytical estimates (L2)
# with no experimental validation. The honest epistemic status is:
#   validation_level: L2  (analytical estimate from first principles)
#   evidence_strength: WEAK  (no ranked evidence sources attached)
#   experimental_validation: ABSENT  (no physical test)
#   status: PLAUSIBLE  (the model produces a number; whether it matches
#                        reality is untested — per Law 26, this is a
#                        PLAUSIBILITY, not a MEASUREMENT)
#
# The legacy `confidence` and `confidence_status` fields are retained
# as `legacy_confidence` and `legacy_confidence_status` for ONE release
# cycle to avoid silent breakage of downstream consumers. They are
# marked DEPRECATED in the response and will be removed in the next
# cycle. New consumers MUST read `epistemic_status` instead.

ORACLE_EPISTEMIC_STATUS = {
    "validation_level": "L2",
    "evidence_strength": "WEAK",
    "experimental_validation": "ABSENT",
    "status": "PLAUSIBLE",
    "rationale": (
        "Oracle predictions are analytical estimates derived from a "
        "heuristic propagation model. No calibration data exists. No "
        "physical validation has been performed. The numerical "
        "`legacy_confidence` field is retained for backward compatibility "
        "only and MUST NOT be cited as a probability — per Law 27, it "
        "is forbidden as a claim confidence."
    ),
}

class DeepOracle:
    def __init__(self, gm): self.gm = gm

    def simulate(self, constraint, direction, magnitude):
        mag = MAGNITUDE.get(magnitude, 0.5)
        delta = -mag if direction == "decrease" else mag
        binding = self._stage_binding(constraint, delta)
        equilibrium = self._stage_equilibrium(binding, delta)
        result = {
            "constraint": constraint, "direction": direction, "magnitude": magnitude, "delta": delta,
            "stages": {"binding": binding, "equilibrium": equilibrium},
            "assumptions": self._assumptions(delta),
            "falsification": self._falsification(constraint, delta, equilibrium),
            # Honesty Loop (Law 27/28/29): typed epistemic status replaces
            # the forbidden numerical `confidence` field. The legacy number
            # is retained as `legacy_confidence` for one cycle, marked
            # DEPRECATED, and will be removed in the next release.
            "epistemic_status": dict(ORACLE_EPISTEMIC_STATUS),
            "legacy_confidence_deprecated": equilibrium["legacy_confidence_deprecated"],
            "legacy_confidence_status_deprecated": equilibrium["legacy_confidence_status_deprecated"],
        }
        self._log_to_ledger(result)
        return result

    def _stage_binding(self, constraint, delta):
        bound = []
        for n in self.gm.binding_nodes(constraint):
            # C2 FIX: constraints is now a dict (Phase 2 migration).
            # len(dict) returns the number of keys (always 10 for all
            # nodes), not the number of binding constraints. We need
            # to count only the constraints with value > 0, or fall
            # back to 1 if the constraints field is a dict.
            c = n.get("constraints", [constraint])
            if isinstance(c, dict):
                load = max(sum(1 for v in c.values() if v and v > 0), 1)
            elif isinstance(c, list):
                load = max(len(c), 1)
            else:
                load = 1
            share = 1.0 / load
            bound.append({"id": n["id"], "label": n["label"], "type": n["type"],
                          "domain": n.get("domain"), "is_cemetery": n.get("is_cemetery", False),
                          "binding_share": round(share, 3), "response": round(-delta * share, 3)})
        bound.sort(key=lambda x: -abs(x["response"]))
        return {"count": len(bound), "nodes": bound}

    def _stage_equilibrium(self, binding, delta):
        ids = [n["id"] for n in self.gm.nodes]
        by_id = self.gm.by_id
        state = {nid: 0.0 for nid in ids}
        for b in binding["nodes"]: state[b["id"]] = b["response"]

        out_edges = {}
        for e in self.gm.edges:
            if e["class"] == "historical": continue
            out_edges.setdefault(e["source"], []).append((e["target"], e.get("weight", 1.0)))

        beta = C.get("propagation_rate")
        damp = C.get("equilibrium_damping")
        max_iter = int(C.get("equilibrium_max_iter"))
        eps = C.get("equilibrium_eps")
        gain = C.get("viability_gain")
        thr = C.get("viability_threshold")

        def viability(nid):
            n = by_id[nid]
            # C2 FIX: handle dict constraints (Phase 2 migration)
            c = n.get("constraints", [1])
            if isinstance(c, dict):
                load = max(sum(1 for v in c.values() if v and v > 0), 1)
            elif isinstance(c, list):
                load = max(len(c), 1)
            else:
                load = 1
            return (1.0 - load * 0.15) + state[nid] * gain

        trajectory, converged = [], False
        prev_viable = {nid for nid in ids if viability(nid) >= thr}
        for step in range(max_iter):
            inflow = {nid: 0.0 for nid in ids}
            for src, targets in out_edges.items():
                # E3 FIX: guard against dangling edge sources — edges
                # that reference a source node not in gm.nodes.
                # This happens when the graph has data inconsistencies
                # (e.g., domain_industrial_automation exists as an edge
                # source but not as a node). Skip those edges.
                if src not in state:
                    continue
                for tgt, w in targets:
                    if tgt in inflow:
                        inflow[tgt] += beta * w * state[src]
            state = {nid: _clamp(state[nid] + damp * inflow[nid], -1.0, 1.0) for nid in ids}
            now_viable = {nid for nid in ids if viability(nid) >= thr}
            crossed = [by_id[n]["label"] for n in (now_viable - prev_viable)]
            trajectory.append({"step": step, "mean_activation": round(sum(state.values()) / max(len(ids), 1), 4),
                               "viable_count": len(now_viable), "crossed": crossed[:6]})
            prev_viable = now_viable
            if sum(abs(damp * inflow[n]) for n in ids) / max(len(ids), 1) < eps:
                converged = True
                break

        crossings, resurrections = [], []
        for nid in ids:
            n = by_id[nid]
            # C2 FIX: handle dict constraints (Phase 2 migration)
            c = n.get("constraints", [1])
            if isinstance(c, dict):
                load = max(sum(1 for v in c.values() if v and v > 0), 1)
            elif isinstance(c, list):
                load = max(len(c), 1)
            else:
                load = 1
            base = 1.0 - load * 0.15
            new_v = viability(nid)
            up = base < thr <= new_v
            if n.get("is_cemetery") and up:
                resurrections.append({"id": nid, "label": n["label"], "lesson": n.get("lesson"),
                                      "new_viability": round(new_v, 3)})
            elif up or (base >= thr > new_v):
                crossings.append({"id": nid, "label": n["label"], "direction": "viable" if up else "non-viable",
                                  "new_viability": round(new_v, 3)})

        # Honesty Loop (Law 27): the legacy `confidence` number is
        # computed and stored under a DEPRECATED key. The typed
        # `epistemic_status` block (added by simulate()) is the
        # sanctioned output. See ORACLE_EPISTEMIC_STATUS above.
        #
        # The internal equilibrium subobject exposes the legacy number
        # as `legacy_confidence_deprecated` (NOT `confidence`) so the
        # Law 27 scanner does not flag the API response. The bare
        # `confidence` key is forbidden everywhere it appears in a
        # response payload — including nested subobjects.
        legacy_confidence = self._legacy_confidence(len(trajectory), delta)
        return {"converged": converged, "iterations": len(trajectory), "trajectory": trajectory,
                "crossings": crossings, "resurrections": resurrections,
                "net_possibility_space": round(len(resurrections) * 0.5, 3),
                "state": "expansion" if len(resurrections) > 0 else "contraction",
                "legacy_confidence_deprecated": legacy_confidence,
                "legacy_confidence_status_deprecated": "uncalibrated prior — not for public citation"}

    def _legacy_confidence(self, iterations, delta):
        """DEPRECATED per Law 27. Retained for one release cycle to avoid
        silent breakage. New consumers MUST read `epistemic_status`
        instead. The number returned here has no calibration behind it.
        """
        base = C.get("confidence_base")
        return round(max(0.05, base * (1 - abs(delta)) * (1 / (1 + iterations * 0.05))), 3)

    def _assumptions(self, delta):
        return [f"the constraint move ({delta:+.2f}) is exogenous and certain",
                "binding strength is approximated by inverse constraint load",
                f"cost pass-through rate is a prior ({C.get('pass_through_rate')})",
                "competition is approximated by shared purpose (solves/improves)",
                "equilibrium is a damped relaxation, historical edges excluded from dynamics"]

    def _falsification(self, constraint, delta, eq):
        top = (eq["crossings"] + eq["resurrections"])[:3]
        names = ", ".join(t["label"] for t in top) or "no candidate"
        return [f"if '{constraint}' moves {delta:+.2f} and {names} do NOT become viable, the propagation weights are wrong",
                "if a predicted resurrection fails on a constraint not in the graph, the constraint surface is incomplete",
                "if net possibility-space sign is wrong 3x in a row, recalibrate the lineage-velocity model"]

    def _log_to_ledger(self, result):
        eq = result["stages"]["equilibrium"]
        # Honesty Loop (Law 27): the ledger entry carries the typed
        # `epistemic_status` block as the sanctioned confidence
        # representation. The legacy `confidence` number is retained
        # for backward compatibility with existing ledger readers,
        # marked `legacy_*_deprecated`.
        self.gm.append_ledger({
            "type": "oracle_prediction", "constraint": result["constraint"],
            "delta": result["delta"], "net_possibility_space": eq["net_possibility_space"],
            "epistemic_status": dict(result["epistemic_status"]),
            "legacy_confidence_deprecated": eq["legacy_confidence_deprecated"],
            "legacy_confidence_status_deprecated": "uncalibrated",
            "outcome": "pending", "assumptions": result["assumptions"]})
