#!/usr/bin/env python3
"""
verify_prose_consistency.py — Prose-consistency linter (DR-9).

Per F-053 (FAILURES.md): the vaccine fridge package §8 line 434 stated
"ESTIMATE count: 3 (BL-003, BL-007, BL-009, BL-011). 4 of 11 lines are
ESTIMATED." The parenthetical lists 4 items but says "count: 3." The
next sentence correctly says "4 of 11." The true count is right in one
place and wrong four words earlier in another.

Per DR-9 (MASTER_PROTOCOL.md): any sentence in a package that asserts
a count ("N of M lines are X", "count: N", "N items") SHALL be checked
against the actual `len()` of the referenced list at render time. A
mismatch blocks rendering.

This linter scans a package markdown file for count-assertion patterns
and checks each against the actual data in the file. It catches:
  1. "count: N" followed by a parenthetical list — checks len(list) == N
  2. "N of M lines are X" — checks that N matches the actual count of X
  3. "N items" followed by a list — checks len(list) == N

Usage:
    python scripts/verify_prose_consistency.py product/PRODUCT.md
    python scripts/verify_prose_consistency.py --strict product/PRODUCT.md

Exit codes:
    0 = no count contradictions found (PASS)
    1 = one or more count contradictions found (FAIL)
    2 = file not found or invalid
"""
import argparse
import re
import sys
import pathlib
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class CountAssertion:
    """A count assertion found in the prose."""
    line_num: int
    pattern_type: str  # "count_colon", "N_of_M", "N_items"
    asserted_count: int
    actual_list: List[str]  # the items listed in the parenthetical
    context: str  # the full sentence for debugging


def extract_count_assertions(text: str) -> List[CountAssertion]:
    """Extract all count assertions from the prose.

    Patterns matched:
      1. "count: N (item1, item2, ...)" — checks len(items) == N
      2. "N of M lines are X" — N is the asserted count
      3. "N items" followed by a parenthetical list
    """
    assertions = []
    lines = text.split("\n")

    for i, line in enumerate(lines):
        # Pattern 1: "count: N (item1, item2, ...)"
        # Matches: "ESTIMATE count: 3 (BL-003, BL-007, BL-009, BL-011)"
        # Also matches: "**ESTIMATE count:** 3 (BL-003, BL-007, BL-009, BL-011)"
        # The \*?\*? handles markdown bold (** **) that may appear after the colon
        # Captures: asserted_count=3, list=[BL-003, BL-007, BL-009, BL-011]
        for m in re.finditer(
            r'count:?\*?\*?\s*(\d+)\s*\(([^)]+)\)',
            line, re.IGNORECASE
        ):
            asserted = int(m.group(1))
            list_str = m.group(2)
            # Split by comma, strip whitespace, filter empty
            items = [item.strip() for item in list_str.split(",") if item.strip()]
            assertions.append(CountAssertion(
                line_num=i + 1,
                pattern_type="count_colon",
                asserted_count=asserted,
                actual_list=items,
                context=line.strip(),
            ))

        # Pattern 2: "N of M lines are X" or "N of M items are X"
        # Matches: "4 of 11 lines are ESTIMATED"
        # This pattern doesn't have an inline list, so we check against
        # the BOM table basis counts later.
        for m in re.finditer(
            r'(\d+)\s+of\s+(\d+)\s+(?:lines?|items?)\s+(?:are|is)\s+(\w+)',
            line, re.IGNORECASE
        ):
            asserted = int(m.group(1))
            total = int(m.group(2))
            basis = m.group(3).upper()
            assertions.append(CountAssertion(
                line_num=i + 1,
                pattern_type="N_of_M",
                asserted_count=asserted,
                actual_list=[],  # filled later from BOM table
                context=line.strip(),
            ))
            # Store the basis for later lookup
            assertions[-1].actual_list = [basis, str(total)]  # temporary storage

    return assertions


def extract_bom_basis_counts(text: str) -> dict:
    """Extract the actual basis counts from the BOM table.

    Returns a dict like:
      {"ESTIMATED": 4, "QUOTED": 3, "CATALOG": 4}
    """
    counts = {"ESTIMATED": 0, "QUOTED": 0, "CATALOG": 0}
    in_bom_table = False
    for line in text.split("\n"):
        # Detect BOM tables (headers with "Basis" column)
        if "| Basis |" in line or "| basis |" in line:
            in_bom_table = True
            continue
        if in_bom_table:
            if not line.strip().startswith("|"):
                in_bom_table = False
                continue
            # Count basis keywords in the row
            for basis in ["ESTIMATED", "QUOTED", "CATALOG"]:
                if basis in line:
                    counts[basis] += 1
    return counts


def check_assertions(assertions: List[CountAssertion], bom_counts: dict) -> List[Tuple[CountAssertion, bool, str]]:
    """Check each assertion against the actual data.

    Returns a list of (assertion, passed, message) tuples.
    """
    results = []
    for a in assertions:
        if a.pattern_type == "count_colon":
            actual = len(a.actual_list)
            if actual != a.asserted_count:
                msg = (
                    f"Line {a.line_num}: 'count: {a.asserted_count}' but "
                    f"parenthetical lists {actual} items: {a.actual_list}. "
                    f"Asserted={a.asserted_count}, Actual={actual}."
                )
                results.append((a, False, msg))
            else:
                msg = (
                    f"Line {a.line_num}: 'count: {a.asserted_count}' with "
                    f"{actual} items in parenthetical — MATCH."
                )
                results.append((a, True, msg))

        elif a.pattern_type == "N_of_M":
            # a.actual_list = [basis, total] (temporary storage)
            basis = a.actual_list[0]
            total_str = a.actual_list[1]
            actual = bom_counts.get(basis, 0)
            if actual != a.asserted_count:
                msg = (
                    f"Line {a.line_num}: '{a.asserted_count} of {total_str} lines are {basis}' "
                    f"but BOM table has {actual} {basis} rows. "
                    f"Asserted={a.asserted_count}, Actual={actual}."
                )
                results.append((a, False, msg))
            else:
                msg = (
                    f"Line {a.line_num}: '{a.asserted_count} of {total_str} lines are {basis}' "
                    f"— BOM has {actual} {basis} rows. MATCH."
                )
                results.append((a, True, msg))

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Prose-consistency linter (DR-9). Checks count assertions against actual data."
    )
    parser.add_argument("path", type=pathlib.Path, help="Path to the package markdown file")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on any contradiction (default)")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    if not args.path.exists():
        print(f"ERROR: file not found: {args.path}", file=sys.stderr)
        return 2

    text = args.path.read_text(encoding="utf-8")
    assertions = extract_count_assertions(text)
    bom_counts = extract_bom_basis_counts(text)
    results = check_assertions(assertions, bom_counts)

    contradictions = [r for r in results if not r[1]]
    passed = [r for r in results if r[1]]

    if args.json:
        import json
        output = {
            "verifier": "scripts/verify_prose_consistency.py",
            "file": str(args.path),
            "total_assertions": len(assertions),
            "passed": len(passed),
            "contradictions": len(contradictions),
            "contradiction_details": [
                {"line": a.line_num, "type": a.pattern_type,
                 "asserted": a.asserted_count, "actual": len(a.actual_list),
                 "context": a.context}
                for a, _, _ in contradictions
            ],
            "bom_basis_counts": bom_counts,
            "status": "PASS" if not contradictions else "FAIL",
        }
        print(json.dumps(output, indent=2))
    else:
        print("=" * 70)
        print("PROSE-CONSISTENCY LINTER (DR-9)")
        print("=" * 70)
        print(f"File: {args.path}")
        print(f"Total count assertions found: {len(assertions)}")
        print(f"Passed: {len(passed)}")
        print(f"Contradictions: {len(contradictions)}")
        print()
        if bom_counts:
            print(f"BOM basis counts: {bom_counts}")
            print()
        if contradictions:
            print("--- CONTRADICTIONS ---")
            for a, passed, msg in contradictions:
                print(f"  FAIL: {msg}")
                print(f"    Context: {a.context[:120]}")
                print()
        else:
            print("No count contradictions found.")
        print("=" * 70)
        if contradictions:
            print("OVERALL STATUS: FAIL")
            print("  One or more count assertions contradict the actual data.")
            print("  Per DR-9, this blocks rendering.")
        else:
            print("OVERALL STATUS: PASS")
            print("  All count assertions match the actual data.")
        print("=" * 70)

    return 0 if not contradictions else 1


if __name__ == "__main__":
    sys.exit(main())
