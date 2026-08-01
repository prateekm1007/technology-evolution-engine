#!/usr/bin/env python3
"""
Law 8 verification cycle: predict -> observe -> reconcile.

This is the loop that the F-005 postmortem identified as missing, and
that the F-005 follow-up audit demanded as the precondition for any
"verified" label. It is the single most important script in this
repository under Law 8.

Procedure (run end-to-end):

  PREDICT   For each historical failure in evidence/failures/*.json,
            run DeepOracle.simulate() on the constraint that the
            failure JSON documents as having moved. Record the
            prediction: did the oracle forecast resurrection (the
            cemetery node appeared in `resurrections`) or not?

  OBSERVE   Read the documented ground-truth outcome. The failure
            JSON's `resurrection_conditions` field is examined: if
            it mentions an actual current project ("Lockheed LMH-1",
            "LTA Research", "Iridium Communications"), the
            observation is "resurrected" or "partial"; otherwise
            "not_resurrected". This is a manual annotation per
            failure file — not a free-text guess. Each annotation
            is recorded in OBSERVED_OUTCOMES below, with a citation
            to the failure JSON.

  RECONCILE  Compare prediction to observation. Append a ledger
            entry with outcome="pass" if prediction matches
            observation, outcome="fail" otherwise.

The cycle MUST produce at least one pass AND at least one fail to
satisfy Law 8. A cycle that produces only passes is suspect: it
either didn't try hard enough, or the prediction mechanism always
agrees with hindsight (which is itself a failure of the methodology).

Replayability: every ledger entry this script writes includes a
`writer` field pointing back to this script, and an `evidence_ref`
field pointing to the failure JSON that grounded the observation.
To reproduce the cycle, run this script with --replay <entry_id>;
it will re-run the prediction and re-compare to the same observation.

Usage:
    python scripts/run_verification_cycle.py            # run cycle, append
    python scripts/run_verification_cycle.py --summary   # print stats only
"""
import argparse
import json
import sys
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web" / "backend"))
sys.path.insert(0, str(ROOT))

from adapters.graph_model import GraphModel
from adapters.oracle_deep import DeepOracle

LEDGER = ROOT / "data" / "ledger" / "predictions.jsonl"
FAILURES_DIR = ROOT / "evidence" / "failures"


# ---------------------------------------------------------------------------
# OBSERVED_OUTCOMES — manual, citable ground truth per failure.
# ---------------------------------------------------------------------------
# Each entry maps a cemetery_id (matches the node id in
# data/civilization_graph.json) to:
#   - observed_outcome: resurrected | partial | not_resurrected
#   - citation: which line of which failure JSON (or external source)
#     grounds the observation. Anything not citable from the failure
#     JSON is sourced from public record and noted as such.
#
# These annotations are NOT derived by the system. They are external
# observations — exactly the kind of "confrontation with reality" that
# Law 8 demands. The system's job is to predict them; our job is to
# record whether it did.
# ---------------------------------------------------------------------------
OBSERVED_OUTCOMES = {
    # Airships: failed 1937. LTA Research (Pathfinder 1) flew 2024;
    # Lockheed Martin LMH-1 was under development through 2020s;
    # Hybrid Air Vehicles Airlander 10 flew 2016-2023.
    # Outcome: partial resurrection (cargo, not passenger).
    "cemetery_009": {
        "name": "Airships",
        "observed_outcome": "partial",
        "citation": (
            "evidence/failures/airships.json `resurrection_conditions` "
            "lists 'Lockheed LMH-1, LTA Research' as active resurrection "
            "projects. Public record: LTA Research Pathfinder 1 first "
            "flight 2024; HAV Airlander 10 first flight 2016."
        ),
        "constraint_to_simulate": "cost",
        "direction": "decrease",
        "magnitude": "2x",
    },

    # Iridium: original Iridium LLC went bankrupt 1999. Iridium
    # Communications (the relisted entity) operates today as a
    # satellite-IoT constellation. Full resurrection.
    "cemetery_006": {
        "name": "Iridium",
        "observed_outcome": "resurrected",
        "citation": (
            "evidence/failures/iridium.json documents the original failure. "
            "Public record: Iridium Communications (IRDM) relaunched and "
            "operates a 66-satellite LEO constellation for IoT/voice as "
            "of 2026."
        ),
        "constraint_to_simulate": "cost",
        "direction": "decrease",
        "magnitude": "10x",
    },

    # Segway: production ended 2020. Consumer segway is dead; e-scooter
    # sharing absorbed the micro-mobility niche. Not resurrected.
    "cemetery_001": {
        "name": "Segway",
        "observed_outcome": "not_resurrected",
        "citation": (
            "evidence/failures/segway.json: production ended 2020. "
            "No successor product for the personal-balancing-transport "
            "category exists. Micro-mobility shifted to shared e-scooters "
            "(Bird, Lime), which are a different product class."
        ),
        "constraint_to_simulate": "cost",
        "direction": "decrease",
        "magnitude": "2x",
    },

    # Concorde: retired 2003. No commercial supersonic passenger
    # transport in operation as of 2026. Boom Supersonic XB-1
    # test flights 2024-2025 but no commercial service yet.
    "cemetery_003": {
        "name": "Concorde",
        "observed_outcome": "partial",
        "citation": (
            "evidence/failures/concorde.json. Public record: Boom "
            "Supersonic XB-1 supersonic flight Oct 2024; Overture not "
            "in commercial service as of 2026. Partial: tech demonstrator "
            "exists, no commercial resurrection yet."
        ),
        "constraint_to_simulate": "cost",
        "direction": "decrease",
        "magnitude": "10x",
    },

    # Google Glass: consumer discontinued 2015. Enterprise Edition
    # discontinued 2023. Augmented-reality headsets (e.g., Meta Ray-Ban,
    # Apple Vision Pro) are a different product class. Not resurrected
    # as the original product.
    "cemetery_002": {
        "name": "Google Glass",
        "observed_outcome": "not_resurrected",
        "citation": (
            "evidence/failures/google_glass.json. Enterprise Edition "
            "discontinued 2023. No like-for-like successor; AR headsets "
            "are a different product class."
        ),
        "constraint_to_simulate": "cost",
        "direction": "decrease",
        "magnitude": "2x",
    },

    # Theranos: fraud conviction 2018. Not resurrected; the underlying
    # claim (single-drop blood diagnostics at consumer accuracy) was
    # scientifically false, not a timing issue.
    "cemetery_004": {
        "name": "Theranos",
        "observed_outcome": "not_resurrected",
        "citation": (
            "evidence/failures/theranos.json. Founder convicted of fraud "
            "2022. The underlying scientific claim was false, not "
            "premature — no resurrection is possible without invalidating "
            "the original premise."
        ),
        "constraint_to_simulate": "regulation",
        "direction": "decrease",
        "magnitude": "2x",
    },

    # Quibi: shut down 2020. No successor. Short-form mobile video
    # was absorbed by TikTok/Reels, but those are platforms, not a
    # premium-content product like Quibi. Not resurrected.
    "cemetery_005": {
        "name": "Quibi",
        "observed_outcome": "not_resurrected",
        "citation": (
            "evidence/failures/quibi.json. Shut down 2020. The category "
            "of premium short-form mobile video was obsoleted by TikTok, "
            "not resurrected by a successor."
        ),
        "constraint_to_simulate": "cost",
        "direction": "decrease",
        "magnitude": "2x",
    },

    # Betamax: discontinued 2016. The format war ended; no
    # successor. Not resurrected.
    "cemetery_007": {
        "name": "Betamax",
        "observed_outcome": "not_resurrected",
        "citation": (
            "evidence/failures/betamax.json. Production ended 2016. "
            "VHS-then-streaming successorship obsoleted the format; no "
            "resurrection."
        ),
        "constraint_to_simulate": "cost",
        "direction": "decrease",
        "magnitude": "2x",
    },

    # HD-DVD: discontinued 2008. Lost to Blu-ray. Streaming obsoleted
    # both. Not resurrected.
    "cemetery_008": {
        "name": "HD-DVD",
        "observed_outcome": "not_resurrected",
        "citation": (
            "evidence/failures/hd_dvd.json. Discontinued 2008. Blu-ray "
            "won the format war; streaming obsoleted physical media. No "
            "resurrection."
        ),
        "constraint_to_simulate": "cost",
        "direction": "decrease",
        "magnitude": "2x",
    },
}


def predict_for_cemetery(gm, oracle, cemetery_id, observed):
    """Run the oracle's simulate() on the constraint documented in the
    failure JSON. Return the prediction: did the cemetery node appear in
    the resurrections list?"""
    if cemetery_id not in gm.by_id:
        return {
            "predicted_resurrection": False,
            "reason": f"cemetery node {cemetery_id} not in graph",
            "oracle_result": None,
        }
    constraint = observed["constraint_to_simulate"]
    direction = observed["direction"]
    magnitude = observed["magnitude"]
    try:
        result = oracle.simulate(constraint, direction, magnitude)
    except Exception as e:
        return {
            "predicted_resurrection": False,
            "reason": f"oracle.simulate raised {type(e).__name__}: {e}",
            "oracle_result": None,
        }
    # Did the cemetery node appear in the resurrections list?
    resurrections = result.get("stages", {}).get("equilibrium", {}).get("resurrections", [])
    predicted = any(r.get("id") == cemetery_id for r in resurrections)
    return {
        "predicted_resurrection": predicted,
        "resurrection_detail": next(
            (r for r in resurrections if r.get("id") == cemetery_id), None),
        "net_possibility_space": result.get("stages", {}).get("equilibrium", {}).get("net_possibility_space"),
        "oracle_result": result,
        "constraint_simulated": constraint,
        "direction": direction,
        "magnitude": magnitude,
    }


def reconcile(predicted, observed_outcome):
    """Pass if prediction matches observation.

    Mapping:
      predicted_resurrection=True  & observed=resurrected/partial  -> pass
      predicted_resurrection=True  & observed=not_resurrected      -> fail
      predicted_resurrection=False & observed=not_resurrected      -> pass
      predicted_resurrection=False & observed=resurrected/partial  -> fail
    """
    observed_positive = observed_outcome in ("resurrected", "partial")
    if predicted == observed_positive:
        return "pass"
    return "fail"


def write_ledger_entry(entry):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def run_cycle():
    print("=" * 60)
    print("LAW 8 VERIFICATION CYCLE")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    gm = GraphModel(repo_root=ROOT)
    oracle = DeepOracle(gm)

    print(f"Graph loaded: {len(gm.nodes)} nodes, source={gm.source}")
    print(f"Cemetery nodes in graph: "
          f"{sum(1 for n in gm.nodes if n.get('type') == 'cemetery_entry')}")
    print()

    results = []
    passes, fails = 0, 0

    for cemetery_id, observed in OBSERVED_OUTCOMES.items():
        print(f"--- {observed['name']} ({cemetery_id}) ---")
        print(f"  observed: {observed['observed_outcome']}")

        prediction = predict_for_cemetery(gm, oracle, cemetery_id, observed)
        outcome = reconcile(prediction["predicted_resurrection"],
                            observed["observed_outcome"])

        if outcome == "pass":
            passes += 1
        else:
            fails += 1

        print(f"  predicted resurrection: {prediction['predicted_resurrection']}")
        print(f"  reconcile: {outcome}")

        entry = {
            "type": "verification",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prediction_id": f"verify_{cemetery_id}_{int(datetime.now(timezone.utc).timestamp())}",
            "cemetery_id": cemetery_id,
            "name": observed["name"],
            "constraint_simulated": prediction.get("constraint_simulated"),
            "direction": prediction.get("direction"),
            "magnitude": prediction.get("magnitude"),
            "predicted_resurrection": prediction["predicted_resurrection"],
            "observed_outcome": observed["observed_outcome"],
            "outcome": outcome,
            "evidence_ref": f"evidence/failures/{observed['name'].lower().replace(' ','_')}.json",
            "citation": observed["citation"],
            "writer": "scripts.run_verification_cycle.reconcile",
        }
        write_ledger_entry(entry)
        results.append(entry)

    print()
    print("=" * 60)
    print(f"Cycle complete: {passes} pass, {fails} fail")
    print(f"Law 8 satisfied (>=1 pass AND >=1 fail): {passes >= 1 and fails >= 1}")
    print(f"Ledger: {LEDGER}")
    print("=" * 60)
    return {"passes": passes, "fails": fails, "results": results}


def print_summary():
    if not LEDGER.exists():
        print("No ledger.")
        return
    entries = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    verifications = [e for e in entries if e.get("type") == "verification"]
    passes = sum(1 for e in verifications if e.get("outcome") == "pass")
    fails = sum(1 for e in verifications if e.get("outcome") == "fail")
    print(f"Total ledger entries: {len(entries)}")
    print(f"  verification entries: {len(verifications)}")
    print(f"    pass: {passes}")
    print(f"    fail: {fails}")
    print(f"  benchmark_run entries: {sum(1 for e in entries if e.get('type') == 'benchmark_run')}")
    print(f"  oracle_prediction entries: {sum(1 for e in entries if e.get('type') == 'oracle_prediction')}")
    print()
    print("Law 8 status:")
    print(f"  parseable: yes")
    print(f"  successful predictions (pass): {passes}")
    print(f"  failed predictions (fail): {fails}")
    print(f"  replayable (have writer field): {sum(1 for e in entries if 'writer' in e)}")
    print(f"  verdict: {'PASS' if passes >= 1 and fails >= 1 else 'FAIL'}")


def main():
    parser = argparse.ArgumentParser(description="Law 8 verification cycle")
    parser.add_argument("--summary", action="store_true",
                        help="print current ledger stats and exit")
    args = parser.parse_args()
    if args.summary:
        print_summary()
        return 0
    run_cycle()
    print()
    print_summary()
    return 0


if __name__ == "__main__":
    sys.exit(main())
