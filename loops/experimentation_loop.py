"""
Loop 4 — Experimentation.

    system proposes blueprint
            ↓
    experiment is executed
            ↓
    measurements are recorded
            ↓
    system updates model

STATUS: OPEN.

This loop requires external collaboration — someone (a human, a
lab, an external team) must execute an experiment that the system
proposes. The system cannot close this loop by itself.

The honest declaration here is:
  - The system can propose experiments (Layer 8 in the 11-layer
    pipeline already does this).
  - The system can record measurements once they're provided
    (the verification ledger accepts entries with type="verification"
    and outcome="pass"|"fail").
  - The system can update its models once outcomes are recorded
    (the depth-upgrade pattern from CTO review #2).
  - But no experiment has been proposed-and-executed-and-recorded
    in a single closed cycle, because no external collaborator has
    executed an experiment the system proposed.

The next_action to close this loop: pick a small experiment the
system can propose (e.g., "test whether a specific lithium-mediated
nitrogen reduction catalyst achieves >=1% Faradaic efficiency at
ambient conditions"), find a collaborator willing to run it, and
record the outcome when it arrives.
"""


class ExperimentationLoop:
    """Loop 4: propose experiment, run it, record, update model."""

    LOOP_NAME = "experimentation"
    LOOP_NUMBER = 4

    def status(self) -> dict:
        return {
            "loop_name": self.LOOP_NAME,
            "loop_number": self.LOOP_NUMBER,
            "closed": False,
            "cycles_completed": 0,
            "reason": (
                "OPEN — experimentation requires an external collaborator "
                "to execute an experiment the system proposes. The system "
                "can propose experiments (Layer 8 of the 11-layer pipeline) "
                "and can record outcomes (verification ledger), but no "
                "experiment has been proposed-and-executed-and-recorded in "
                "a single closed cycle. That requires a human or external "
                "lab to run the experiment."
            ),
            "infrastructure_present": [
                "invention_compiler/verification_engine.py (Layer 8: proposes experiments)",
                "hypothesis/Hypothesis (record experimental outcomes)",
                "scripts/run_verification_cycle.py (reconcile outcomes)",
            ],
            "infrastructure_missing": [
                "external collaborator to execute proposed experiments",
                "first experiment cycle proposed, executed, and recorded",
            ],
            "next_action_to_close": (
                "Pick a small experiment the system can propose (e.g., "
                "'test whether a specific lithium-mediated nitrogen "
                "reduction catalyst achieves >=1% Faradaic efficiency at "
                "ambient conditions'). Find a collaborator willing to run "
                "it. When the outcome arrives, record it in the ledger. "
                "Loop 4 will be closed when at least one such cycle is "
                "complete."
            ),
        }

    def run_one_cycle(self) -> dict:
        """Propose an experiment. Does NOT close the loop — only an
        external collaborator running the experiment can do that."""
        from hypothesis.hypothesis import Hypothesis
        proposal = Hypothesis(
            claim=(
                "A lithium-mediated nitrogen reduction catalyst with "
                "ethylene glycol electrolyte achieves >=1% Faradaic "
                "efficiency for NH3 production at ambient conditions."
            ),
            confidence=0.20,
            evidence=[
                "electrochemical_ammonia pathway (chemistry_knowledge_module)",
                "lithium-mediated mechanism documented in literature",
                "ambient conditions constraint",
            ],
            writer="loops.experimentation_loop.run_one_cycle",
        )
        return {
            "loop_name": self.LOOP_NAME,
            "experiment_proposed": proposal.to_dict(),
            "next_step": (
                "External collaborator must execute this experiment and "
                "report the outcome. Loop 4 is NOT closed until the "
                "outcome is recorded in the ledger."
            ),
        }
