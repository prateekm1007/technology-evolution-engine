#!/usr/bin/env python3
"""PSCD-1 AI Loop entrypoint. Fail-closed by default."""
import sys, argparse, json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pscd.ai_loop import RoundController, RoundState, run_dry_run_loop


def main():
    parser = argparse.ArgumentParser(description="PSCD-1 AI Discovery Loop")
    parser.add_argument("--create-round", action="store_true")
    parser.add_argument("--freeze-evidence", action="store_true")
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--commit-predictions", action="store_true")
    parser.add_argument("--import-outcomes", action="store_true")
    parser.add_argument("--score", action="store_true")
    parser.add_argument("--learn", action="store_true")
    parser.add_argument("--prepare-next-round", action="store_true")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Run full dry-run loop")
    args = parser.parse_args()

    if args.dry_run:
        result = run_dry_run_loop()
        print(json.dumps(result, indent=2, default=str))
        return

    if args.status:
        print("PSCD-1 AI Loop Status:")
        print(f"  SCIENTIFIC_EXECUTION_PERMITTED: FALSE (REAL_SEAL_READY=FALSE)")
        print(f"  A2_AUTHORIZATION_REQUESTED: FALSE")
        print(f"  States: 11 normal + ABORTED = 12 total")
        return

    if not any([args.create_round, args.freeze_evidence, args.generate,
                args.commit_predictions, args.import_outcomes, args.score,
                args.learn, args.prepare_next_round, args.audit]):
        parser.print_help()
        print("\nDefault behavior: fail-closed. No action without explicit command.")
        return

    print("Command not yet implemented for production use.")
    print("Use --dry-run for plumbing test.")
    sys.exit(1)


if __name__ == "__main__":
    main()
