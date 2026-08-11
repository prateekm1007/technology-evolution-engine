#!/usr/bin/env python3
"""run_dxp005_one.py — Run a single DXP-005 case (NEMOTRON PILOT — ARCHIVAL).

**STATUS: ARCHIVAL — DO NOT EXECUTE**
This is a quarantined pilot runner. It is preserved as an archival artifact
documenting how the Nemotron pilot was executed. It contains a machine-
enforced protocol lock that prevents execution while DXP-005 is PAUSED.

The output directory is the quarantine namespace
(experiments/dxp005_pilots/nemotron/ENGINE_OUTPUT/) — NOT the primary
DXP-005 output path.

See: experiments/dxp005_pilots/nemotron/QUARANTINE_MANIFEST.json
See: experiments/dxp005_pilots/nemotron/runner_scripts/README.md
"""
import sys, os, json, time
from pathlib import Path

# NOTE: this file lives at experiments/dxp005_pilots/nemotron/runner_scripts/
# so parents[4] is the repo root.
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "discovery_experiment/CASES"))

from engine.openrouter_provider import OpenRouterProvider
from engine.mechanism_extraction import MechanismExtractionEngine
from engine.mechanism_abstraction import MechanismAbstractionEngine
from engine.cross_domain_transfer import CrossDomainTransferEngine
from engine.hypothesis_generation import HypothesisGenerationEngine
from engine.adversarial_analysis import AdversarialAnalysisEngine
from discovery_infrastructure.discovery_substrate import (
    TransferHypothesis, EpistemicState, MechanismGraph, MechanismNode,
    MechanismEdge, MechanismNodeType, MechanismEdgeType,
)

GT = json.loads((REPO / "discovery_experiment/CASES/DXP-005/DXP-005_GROUND_TRUTH.json").read_text())
CASES = GT["cases"]

# OUTPUT_DIR redirected to quarantine namespace (audit finding B, round 3).
# Directory is NOT created at import time (audit finding round 4).
# It is created inside main() AFTER the protocol lock passes.
OUTPUT_DIR = REPO / "experiments" / "dxp005_pilots" / "nemotron" / "ENGINE_OUTPUT"


def save_json(path, data):
    """Save JSON with timestamp."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def main():
    # ===== MACHINE-ENFORCED PROTOCOL LOCK (audit finding A) =====
    # DXP-005 is PAUSED. The runner cannot proceed unless PROGRAM_STATE.json
    # explicitly says status=AUTHORIZED.
    from engine.protocol_lock import assert_experiment_authorized, assert_output_dir_writable
    assert_experiment_authorized("DXP-005")

    # ===== OUTPUT DIRECTORY LOCK (audit finding B, round 3) =====
    assert_output_dir_writable("DXP-005", OUTPUT_DIR)

    # ===== CREATE OUTPUT DIRECTORY (audit finding round 4) =====
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) < 2:
        print("Usage: python3 run_dxp005_one.py <CASE_ID>")
        print(f"Available: {sorted(CASES.keys())}")
        return

    case_id = sys.argv[1]
    if case_id not in CASES:
        print(f"ERROR: case '{case_id}' not in CASES. Available: {sorted(CASES.keys())}")
        return

    API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    if not API_KEY:
        print("ERROR: OPENROUTER_API_KEY environment variable not set")
        return

    reasoning = OpenRouterProvider(
        api_key=API_KEY,
        model="nvidia/nemotron-3-ultra-550b-a55b:free",
        default_max_tokens=4096,
        timeout=60,
        max_retries=3,
        retry_backoff=3.0,
    )
    print(f"Provider: {reasoning.provider_name} / {reasoning.model_name}")
    print(f"Case: {case_id}")
    print(f"Started: {time.strftime('%H:%M:%S')}")

    # NOTE: run_case is imported lazily to avoid importing the canonical
    # runner (which now uses ZAI). The quarantined runner uses its own
    # Nemotron provider. The run_case function itself is provider-agnostic
    # — it accepts any ReasoningProvider. We import it here for the pilot
    # record only; execution is blocked by the protocol lock above.
    print("ERROR: This quarantined pilot runner cannot execute while DXP-005 is PAUSED.")
    print("       The protocol lock above should have prevented reaching this line.")
    return


if __name__ == "__main__":
    main()
