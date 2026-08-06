#!/usr/bin/env python3
"""Immutability Validation (Law 7)."""
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from benchmarks.immutability import save_checksums, verify_integrity
from benchmarks.provenance import validate_all_benchmarks

def main():
    parser = argparse.ArgumentParser(description="TEE Immutability Validation")
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--provenance", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if not args.init and not args.check and not args.provenance: args.all = True
    print("=" * 60)
    print("TEE IMMUTABILITY VALIDATION (Law 7)")
    print("=" * 60)
    rc = 0
    if args.all or args.init:
        print("\n[1] Checksum registry...")
        reg = save_checksums()
        print(f"    {len(reg)} files registered")
    if args.all or args.check:
        print("\n[2] Integrity check...")
        ok, violations = verify_integrity()
        if ok: print("    PASS")
        else:
            print("    FAIL:")
            for v in violations: print(f"      {v}")
            rc = 1
    if args.all or args.provenance:
        print("\n[3] Provenance check...")
        issues = validate_all_benchmarks()
        if not issues: print("    PASS: All benchmarks have complete provenance.")
        else:
            for bid, il in issues.items(): print(f"      {bid}: {il}")
    print("\n" + "=" * 60)
    print("PASSED" if rc == 0 else "FAILED")
    return rc

if __name__ == "__main__":
    sys.exit(main())
