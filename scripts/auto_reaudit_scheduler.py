#!/usr/bin/env python3
"""
auto_reaudit_scheduler.py — Automatic re-audit cadence (DR-68, cycle 198).

Per the roadmap: "Wire reaudit_loop.py into whatever drives the cycle loop
itself, so it fires automatically every N cycles without a human or an
external auditor triggering it."

This module:
1. Checks the current cycle number (from git log).
2. Checks how many cycles since the last re-audit.
3. If ≥10 cycles since last re-audit, runs the re-audit automatically.
4. Logs the result to the predictions ledger.

Usage:
    python3 -m scripts.auto_reaudit_scheduler
"""
import sys
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "data" / "ledger" / "predictions.jsonl"
REAUDIT_INTERVAL = 10  # run every 10 cycles


def get_current_cycle() -> int:
    """Get the current cycle number from git log."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--grep=cycle"],
            capture_output=True, text=True, cwd=str(REPO)
        )
        # Find the highest cycle number
        import re
        cycles = re.findall(r'cycle (\d+)', result.stdout)
        if cycles:
            return max(int(c) for c in cycles)
    except Exception:
        pass
    return 0


def get_last_reaudit_cycle() -> int:
    """Get the cycle number of the last automatic re-audit."""
    if not LEDGER.exists():
        return 0
    last_cycle = 0
    with LEDGER.open() as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("type") == "auto_reaudit":
                    c = entry.get("cycle", 0)
                    if c > last_cycle:
                        last_cycle = c
            except json.JSONDecodeError:
                continue
    return last_cycle


def should_run_reaudit() -> bool:
    """Check if enough cycles have passed since the last re-audit."""
    current = get_current_cycle()
    last = get_last_reaudit_cycle()
    return (current - last) >= REAUDIT_INTERVAL


def run_auto_reaudit() -> dict:
    """Run an automatic re-audit and log the result.

    Returns:
        dict with the re-audit result
    """
    from scripts.reaudit_loop import load_claims, get_eligible_claims, draw_sample, run_world_audit, construct_seed, get_external_entropy
    import subprocess as _sp

    # Load and filter claims
    claims = load_claims()
    eligible = get_eligible_claims(claims)

    # Get commit hash for seed
    try:
        commit_hash = _sp.check_output(["git", "rev-parse", "HEAD"], cwd=str(REPO)).decode().strip()[:12]
    except Exception:
        commit_hash = "unknown"

    # Construct seed for entropy-seeded sampling
    entropy = get_external_entropy()
    seed = construct_seed(get_current_cycle(), commit_hash, entropy)

    # Draw a sample of 3 claims
    sample = draw_sample(eligible, seed, k=min(3, len(eligible)))

    # Re-audit each claim
    results = []
    for claim in sample:
        try:
            result = run_world_audit(claim, claims)
            verdict = result.get("verdict", "UNRESOLVED")
            results.append({
                "claim_id": claim.get("experiment_id", claim.get("observation_id", "unknown")),
                "verdict": verdict,
                "overturned": verdict == "OVERTURNED",
            })
        except Exception as e:
            results.append({
                "claim_id": "error",
                "verdict": "UNRESOLVED",
                "error": str(e)[:100],
            })

    # Log the auto-reaudit
    now = datetime.now(timezone.utc).isoformat()
    current_cycle = get_current_cycle()
    log_entry = {
        "type": "auto_reaudit",
        "timestamp": now,
        "cycle": current_cycle,
        "writer": "scripts.auto_reaudit_scheduler",
        "n_claims_audited": len(results),
        "results": results,
        "trigger": f"automatic (every {REAUDIT_INTERVAL} cycles)",
    }

    with LEDGER.open("a") as f:
        f.write(json.dumps(log_entry, default=str) + "\n")

    return log_entry


def main():
    print("=" * 60)
    print("AUTO RE-AUDIT SCHEDULER (DR-68)")
    print("=" * 60)
    print()

    current = get_current_cycle()
    last = get_last_reaudit_cycle()
    print(f"Current cycle: {current}")
    print(f"Last auto-reaudit cycle: {last}")
    print(f"Cycles since last: {current - last}")
    print(f"Interval: every {REAUDIT_INTERVAL} cycles")
    print()

    if should_run_reaudit():
        print("→ Running automatic re-audit...")
        result = run_auto_reaudit()
        print(f"  Claims audited: {result['n_claims_audited']}")
        for r in result["results"]:
            print(f"    {r['claim_id']}: {r['verdict']}")
        print(f"  Logged to {LEDGER}")
    else:
        print(f"→ Not yet (need {REAUDIT_INTERVAL} cycles since last, have {current - last})")
        print("  Next auto-reaudit will trigger automatically.")


if __name__ == "__main__":
    main()
