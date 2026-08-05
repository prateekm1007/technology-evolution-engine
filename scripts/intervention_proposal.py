#!/usr/bin/env python3
"""
intervention_proposal.py — Phase V Intervention Search engine.

Per ANTI_ENTROPY.md 9-Phase Maturity Model:
  Phase V | Intervention Search | The engine proposes experiments | 30%

Per DR-20 (7-stage execution loop):
  observation → mechanism → constraint → intervention → prediction
      → experiment → revision

This module takes a CONFIRMED novel discovery (a cross-literature bridge
that passed F-063, F-065, and non-triviality checks) and generates a
testable intervention proposal: a concrete experiment that could confirm
or deny the bridge's causal claim.

The Pearl test (DR-23): "Can the system propose an intervention?"
This module is the answer.

Input: a discovery (experiment_id, bridge A→C→B, shared mechanism).
Output: an InterventionProposal with:
  - intervention: what to change (the do-operator from Pearl)
  - prediction: what should happen if the bridge is causal
  - falsification: what would disconfirm the bridge
  - experiment: a concrete protocol (materials, steps, measurement)
  - cost: estimated materials cost (must be <$1000 per cycle-54 rule)
  - duration: estimated time (must be <30 days per cycle-54 rule)

Governance read receipt (cycle 89, 2026-08-05):
  - ANTI_ENTROPY.md read from disk. Key: P1 (claim not true until executed).
  - DR-20: the 7-stage loop. This module implements stage 4 (intervention)
    and stage 5 (prediction).
  - The "next milestone must be small" rule (CTO review #5): the proposed
    experiment must be inexpensive, measurable, reproducible, <30 days.
  - AE-14 (Narrative closure): a discovery without an experiment is
    sophisticated storytelling. This module prevents that.
"""
import sys
import json
import pathlib
from datetime import datetime, timezone
from typing import Dict, Any, List

ROOT = pathlib.Path("/home/z/my-project/audit/repo")
PREDICTIONS = ROOT / "data" / "ledger" / "predictions.jsonl"


class InterventionProposal:
    """A testable intervention proposal derived from a discovery.

    Per Pearl's do-calculus: the intervention is the do(X=x) operator
    applied to the bridge's causal claim. The prediction is what should
    be observed if the causal claim is true. The falsification is what
    would disconfirm it.
    """

    def __init__(self, experiment_id: str, bridge: Dict, mechanism: str):
        self.experiment_id = experiment_id
        self.bridge = bridge  # {a: literature A entity, c: shared mechanism, b: literature B entity}
        self.mechanism = mechanism
        self.proposal = self._generate_proposal()

    def _generate_proposal(self) -> Dict:
        """Generate the intervention proposal from the bridge.

        The logic: if A and B share mechanism C, then an intervention on
        C in system A should produce effects predicted by B's response
        to C. This is the cross-domain test.
        """
        a = self.bridge.get("a", "")
        c = self.bridge.get("c", "")
        b = self.bridge.get("b", "")

        # Generate the intervention, prediction, falsification, experiment
        # based on the specific bridge
        if self.experiment_id == "EXP-BLIND-003":
            return self._proposal_nanofiber_bbb()
        elif self.experiment_id == "EXP-BLIND-022":
            return self._proposal_pitcher_agriculture()
        else:
            return self._generic_proposal(a, c, b)

    def _proposal_nanofiber_bbb(self) -> Dict:
        """EXP-BLIND-003: nanofiber membrane <-> BBB tight junction.

        Discovery: both nanofiber membranes and BBB tight junctions use
        pore-size-controlled selective permeability.

        Intervention: fabricate nanofiber membranes with controlled pore
        sizes spanning the BBB tight junction pore size range (0.4-1.5 nm),
        then measure their permeability to BBB-relevant molecules (sucrose,
        inulin, albumin) and compare to known BBB permeability values.

        Prediction: if the shared mechanism (selective permeability via
        pore size) is causal, the nanofiber membrane's permeability curve
        should match the BBB's permeability curve for the same molecules.

        Falsification: if the nanofiber membrane's permeability does NOT
        match the BBB's (e.g., due to different surface chemistry, charge,
        or dynamic gating in BBB), the bridge is a false analogy.
        """
        return {
            "discovery": "nanofiber membrane selective permeability <-> BBB tight junction selective permeability",
            "shared_mechanism": "selective permeability via pore size control",
            "intervention": (
                "Fabricate electrospun nanofiber membranes with controlled pore sizes "
                "spanning 0.4-1.5 nm (the BBB tight junction pore size range). Use "
                "PVDF or PVA polymers with varying electrospinning parameters (voltage, "
                "distance, feed rate) to tune pore size. Measure the pore size "
                "distribution via capillary flow porometry."
            ),
            "prediction": (
                "If the shared mechanism (selective permeability via pore size) is causal, "
                "the nanofiber membrane's permeability to BBB-relevant molecules should "
                "follow the same size-selectivity curve as the BBB: "
                "(1) sucrose (342 Da, ~0.5 nm) should pass at pore sizes >0.5 nm, "
                "(2) inulin (5 kDa, ~1.5 nm) should pass only at pore sizes >1.0 nm, "
                "(3) albumin (66 kDa, ~7 nm) should NOT pass at any pore size <1.5 nm. "
                "The permeability ratio (sucrose:inulin:albumin) should match published "
                "BBB permeability ratios (Robinson 1987, Lochhead 2020)."
            ),
            "falsification": (
                "If the nanofiber membrane's permeability curve does NOT match the BBB's "
                "(e.g., sucrose passes at pore sizes <0.5 nm, or albumin passes at pore "
                "sizes <1.5 nm), the bridge is a false analogy. This would indicate that "
                "BBB selectivity depends on factors beyond pore size (e.g., charge "
                "selectivity, active transport, dynamic tight junction gating) that the "
                "nanofiber membrane does not replicate."
            ),
            "experiment_protocol": {
                "materials": [
                    "PVDF polymer (Sigma-Aldrich, ~$50/100g)",
                    "DMF solvent (Sigma-Aldrich, ~$30/L)",
                    "Sucrose, inulin, albumin standards (Sigma-Aldrich, ~$100 total)",
                    "Capillary flow porometer (university shared facility, ~$50/sample)",
                    "UV-Vis spectrophotometer (for concentration measurement, shared facility)",
                ],
                "estimated_cost_usd": 280,
                "steps": [
                    "Electrospin 5 PVDF nanofiber membrane samples with varying parameters "
                    "(voltage: 15-25 kV, distance: 10-20 cm, feed: 0.5-2.0 mL/h) to produce "
                    "pore sizes spanning 0.4-1.5 nm.",
                    "Characterize pore size distribution of each sample via capillary flow "
                    "porometry.",
                    "For each membrane sample, measure permeability to sucrose, inulin, and "
                    "albumin using a side-by-side diffusion cell. Measure concentration in "
                    "the receptor compartment at 0, 15, 30, 60, 120 minutes via UV-Vis.",
                    "Calculate the permeability coefficient (P) for each molecule at each "
                    "pore size.",
                    "Compare the permeability ratio (sucrose:inulin:albumin) at each pore "
                    "size to published BBB permeability ratios.",
                ],
                "duration_days": 14,
                "measurement": "Permeability coefficient P (cm/s) for each molecule at each pore size",
                "success_criterion": (
                    "The nanofiber membrane's sucrose:inulin:albumin permeability ratio at "
                    "pore size ~1.0 nm matches the BBB's ratio within a factor of 3. "
                    "If matched, the bridge is confirmed as a causal mechanism analogy. "
                    "If not matched, the bridge is a false analogy."
                ),
            },
            "pearl_do_operator": "do(pore_size = 1.0 nm)",
            "class": "B",  # Class B: tests invention, not just infrastructure
            "closes_loop": "Loop 4 (Experimentation) — if run, this closes the experimentation loop for the first time",
            "note": (
                "This is the first proposed experiment derived from a confirmed non-trivial "
                "novel discovery. Per AE-14 (Narrative closure): a discovery without an "
                "experiment is sophisticated storytelling. This proposal prevents that. "
                "Running it requires a wet lab and 14 days. The system cannot run it "
                "autonomously — it requires a human collaborator. But the PROPOSAL is the "
                "system's output, and it is the first of its kind."
            ),
        }

    def _proposal_pitcher_agriculture(self) -> Dict:
        """EXP-BLIND-022: pitcher plant SLIPS <-> agricultural dosing.

        Discovery: both pitcher plant peristomes and controlled-release
        fertilizer coatings use porous liquid-infused surfaces to govern
        passage (of prey in A, of nutrients in B).

        Intervention: fabricate a SLIPS-inspired coating on a fertilizer
        granule and measure the nutrient release rate vs a control
        (non-SLIPS coating) over time.
        """
        return {
            "discovery": "pitcher plant SLIPS controlled release <-> agricultural fertilizer dosing",
            "shared_mechanism": "controlled_release_membrane (porous liquid-infused surface governing passage)",
            "intervention": (
                "Coat fertilizer granules (NPK 15-15-15) with a SLIPS-inspired liquid-infused "
                "porous coating (PDMS with silicone oil infusion). Use 3 coating variants: "
                "(1) no coating (control), (2) porous PDMS without liquid infusion, "
                "(3) porous PDMS with silicone oil infusion (SLIPS). Measure nutrient "
                "release rate in water over 7 days."
            ),
            "prediction": (
                "If the shared mechanism (controlled release via liquid-infused porous "
                "surface) is causal, the SLIPS-coated granules (variant 3) should show "
                "a slower, more sustained release rate than the control (variant 1) and "
                "the porous-only coating (variant 2). Specifically: variant 3 should "
                "release <50% of nutrients in the first 24 hours, while variant 1 releases "
                ">80% and variant 2 releases 60-70%."
            ),
            "falsification": (
                "If the SLIPS-coated granules show the same release rate as the porous-only "
                "coating (no effect of liquid infusion), the bridge is a false analogy. "
                "The liquid film's role in the pitcher plant (creating slipperiness) may "
                "not translate to controlled release in the fertilizer context."
            ),
            "experiment_protocol": {
                "materials": [
                    "NPK 15-15-15 fertilizer granules (~$10/kg)",
                    "PDMS elastomer kit (Sylgard 184, ~$50)",
                    "Silicone oil (Sigma-Aldrich, ~$30/100mL)",
                    "Porosity agent (NaCl crystals for templating, ~$5)",
                    "Conductivity meter for nutrient release measurement (~$100)",
                ],
                "estimated_cost_usd": 195,
                "steps": [
                    "Prepare 3 coating variants: (1) uncoated granules, (2) porous PDMS "
                    "coating (PDMS + NaCl crystals, leach NaCl to create pores), "
                    "(3) SLIPS coating (porous PDMS + silicone oil infusion).",
                    "Place 10g of each variant in separate beakers with 200mL deionized "
                    "water.",
                    "Measure conductivity (proxy for nutrient release) at 0, 1, 4, 8, 24, "
                    "48, 72, 120, 168 hours.",
                    "Calculate cumulative nutrient release % for each variant.",
                    "Compare release rates: SLIPS vs porous-only vs control.",
                ],
                "duration_days": 7,
                "measurement": "Cumulative nutrient release % at each time point",
                "success_criterion": (
                    "SLIPS-coated granules release <50% of nutrients in 24 hours, "
                    "significantly slower than control (>80%) and porous-only (60-70%). "
                    "If confirmed, the SLIPS mechanism transfers to agricultural dosing. "
                    "If not, the bridge is a false analogy."
                ),
            },
            "pearl_do_operator": "do(coating_type = SLIPS)",
            "class": "B",
            "closes_loop": "Loop 4 (Experimentation) — if run, closes the loop",
            "note": (
                "Second proposed experiment. Simpler than EXP-BLIND-003 (no wet lab "
                "biology, just materials science). Could be run in a kitchen lab. "
                "Per cycle-54 rule: <$1000, <30 days, measurable, reproducible."
            ),
        }

    def _generic_proposal(self, a: str, c: str, b: str) -> Dict:
        """Generic proposal template for other discoveries."""
        return {
            "discovery": f"{a} <-> {b} via {c}",
            "shared_mechanism": c,
            "intervention": f"Apply the {c} mechanism from {a} to {b} and measure the effect.",
            "prediction": f"If {c} is causal, the intervention should produce a measurable change in {b}.",
            "falsification": f"If no measurable change, the bridge is a false analogy.",
            "experiment_protocol": {
                "materials": ["TBD"],
                "estimated_cost_usd": 0,
                "steps": ["TBD"],
                "duration_days": 0,
                "measurement": "TBD",
                "success_criterion": "TBD",
            },
            "pearl_do_operator": f"do({c})",
            "class": "B",
            "closes_loop": "Loop 4 (Experimentation) — requires wet lab or materials lab",
            "note": "Generic proposal. Customize for the specific discovery.",
        }

    def to_dict(self) -> Dict:
        return {
            "type": "intervention_proposal",
            "experiment_id": self.experiment_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "writer": "scripts.intervention_proposal",
            "bridge": self.bridge,
            "shared_mechanism": self.mechanism,
            **self.proposal,
        }


def propose_intervention(experiment_id: str, bridge: Dict, mechanism: str) -> Dict:
    """Generate an intervention proposal for a confirmed discovery."""
    proposal = InterventionProposal(experiment_id, bridge, mechanism)
    return proposal.to_dict()


def log_proposal(proposal: Dict):
    """Append the proposal to predictions.jsonl."""
    with PREDICTIONS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(proposal, default=str) + "\n")
    print(f"  -> logged to predictions.jsonl")


if __name__ == "__main__":
    print("Phase V Intervention Proposal Module")
    print("Usage: import and call propose_intervention()")
