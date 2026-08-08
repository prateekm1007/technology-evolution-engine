#!/usr/bin/env python3
"""run_dxp005_one.py — Run a single DXP-005 case.

Usage: python3 scripts/run_dxp005_one.py <CASE_ID>

Used to run cases one at a time, since long-running background processes
get killed by the shell session.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../discovery_experiment/CASES")

# Import everything from the main runner
from scripts.run_dxp005 import run_case, OUTPUT_DIR, CASES, save_json, generate_final_table
from engine.openrouter_provider import OpenRouterProvider


def main():
    # ===== MACHINE-ENFORCED PROTOCOL LOCK (audit finding A) =====
    # DXP-005 is PAUSED. The runner cannot proceed unless PROGRAM_STATE.json
    # explicitly says status=AUTHORIZED.
    from engine.protocol_lock import assert_experiment_authorized
    assert_experiment_authorized("DXP-005")

    if len(sys.argv) < 2:
        print("Usage: python3 scripts/run_dxp005_one.py <CASE_ID>")
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

    t0 = time.time()
    try:
        result = run_case(case_id, reasoning)
    except Exception as e:
        import traceback
        result = {"case_id": case_id, "status": f"ERROR: {type(e).__name__}: {e}",
                  "traceback": traceback.format_exc()}
        print(f"ERROR: {e}")
        traceback.print_exc()

    t1 = time.time()
    print(f"Elapsed: {t1-t0:.1f}s")

    case_result_file = OUTPUT_DIR / f"{case_id}-result.json"
    save_json(case_result_file, result)

    # Print summary
    if "conditions" in result:
        for cond, cr in result.get("conditions", {}).items():
            print(f"  {case_id}-{cond}: {cr.get('n_hypotheses',0)} hyps, "
                  f"{cr.get('n_survived',0)} survived, {cr.get('n_killed',0)} killed")
    else:
        print(f"  {case_id}: {result.get('status', 'COMPLETED')}")


if __name__ == "__main__":
    main()
