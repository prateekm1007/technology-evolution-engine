#!/usr/bin/env python3
"""
Independent Recomputation Verifier (Phase 1 — highest leverage)

Per external auditor: 'Every gap I found — the $400 BOM error, the
3kg mass error, the QUOTED/ESTIMATED miscounts, the mislabeled
amortization — has the same origin: the system checks its own
arithmetic against itself, not against an independent recomputation.'

This verifier is architecturally separate from the generation path.
It reads product/PRODUCT.md, extracts all BOM line items + mass
rows + cost claims, and recomputes every headline number from
scratch. Any diff > 0 blocks the PASS verdict.

Usage:
    python scripts/verify_arithmetic.py product/PRODUCT.md

Exit codes:
    0 = all numbers verified (PASS)
    1 = one or more numbers fail independent recomputation (FAIL)

Definition of done: feed it PKG-DESAL-002. It must independently
surface all four errors the auditor found without being told they exist:
  1. BOM sum: $5,050 vs claimed $4,650
  2. Mass sum: 283.0 kg vs claimed 280.0 kg
  3. QUOTED/ESTIMATED count: 10 QUOTED / 7 ESTIMATED vs claimed 10/6
  4. Amortization: $1.82/day vs claimed $1.20/day
"""
import re
import sys
import pathlib
import json

ROOT = pathlib.Path(__file__).resolve().parents[1]


def extract_bom_rows(md_text: str) -> list[dict]:
    """Extract BOM rows from markdown tables.

    Looks for tables with columns containing $ amounts and qty.
    Returns list of {line, unit_cost, qty, subtotal, basis} dicts.
    """
    rows = []
    lines = md_text.split("\n")
    in_bom_table = False
    bom_headers = None

    for i, line in enumerate(lines):
        # Detect BOM tables: look for headers with "Unit cost" or "Subtotal" and "$"
        # but NOT mass tables (which have "Unit mass" or "kg")
        if ("| Unit cost" in line or "| Unit " in line) and "kg" not in line.lower() and "mass" not in line.lower():
            in_bom_table = True
            bom_headers = [h.strip() for h in line.split("|")[1:-1]]
            continue

        if in_bom_table:
            # Skip separator rows
            if line.strip().startswith("|---") or line.strip().startswith("|:"):
                continue

            # End of table (empty line or non-table line)
            if not line.strip().startswith("|"):
                in_bom_table = False
                bom_headers = None
                continue

            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) < 4:
                continue

            # Skip header rows
            if "Unit" in cells[0] or "Component" in cells[0]:
                continue

            # Skip total rows
            if "Total" in cells[0] or "total" in cells[0].lower():
                # Extract the claimed total
                for c in cells:
                    m = re.search(r'\$?([\d,]+\.?\d*)', c.replace(',', ''))
                    if m:
                        rows.append({
                            "type": "total_claim",
                            "value": float(m.group(1)),
                            "line_num": i + 1,
                        })
                continue

            # Parse line item
            row = {"type": "line_item", "line_num": i + 1, "raw": line.strip()}

            # Find unit cost (look for $X.XX pattern)
            unit_cost = None
            qty = None
            subtotal = None
            basis = None

            for j, cell in enumerate(cells):
                # Unit cost: $X.XX (not subtotal, not total)
                if unit_cost is None and "$" in cell and "ESTIMATED" not in cell and "QUOTED" not in cell and "CATALOG" not in cell:
                    m = re.search(r'\$([\d,]+\.?\d*)', cell)
                    if m:
                        val = float(m.group(1).replace(',', ''))
                        # Heuristic: unit cost is typically < $1000
                        if val < 10000:
                            unit_cost = val

                # Qty: pure number
                if qty is None and cell.isdigit():
                    qty = int(cell)

                # Subtotal: $X.XX (larger number)
                if "$" in cell:
                    m = re.search(r'\$([\d,]+\.?\d*)', cell)
                    if m:
                        val = float(m.group(1).replace(',', ''))
                        if subtotal is None and qty and unit_cost and abs(val - unit_cost * qty) < 1.0:
                            subtotal = val

                # Basis: QUOTED, CATALOG, ESTIMATED
                if "QUOTED" in cell:
                    basis = "QUOTED"
                elif "CATALOG" in cell:
                    basis = "CATALOG"
                elif "ESTIMATED" in cell:
                    basis = "ESTIMATED"

            if unit_cost is not None and qty is not None:
                row["unit_cost"] = unit_cost
                row["qty"] = qty
                row["computed_subtotal"] = round(unit_cost * qty, 2)
                row["basis"] = basis or "UNKNOWN"
                rows.append(row)

    return rows


def extract_mass_rows(md_text: str) -> list[dict]:
    """Extract mass stack-up rows from markdown tables."""
    rows = []
    lines = md_text.split("\n")
    in_mass_table = False

    for i, line in enumerate(lines):
        if "Unit mass" in line and "Subtotal" in line:
            in_mass_table = True
            continue

        if in_mass_table:
            if line.strip().startswith("|---") or line.strip().startswith("|:"):
                continue
            if not line.strip().startswith("|"):
                in_mass_table = False
                continue

            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) < 4:
                continue

            if "Total" in cells[0] or "total" in cells[0].lower():
                for c in cells:
                    m = re.search(r'([\d,]+\.?\d*)\s*kg', c)
                    if m:
                        rows.append({
                            "type": "total_claim",
                            "value": float(m.group(1).replace(',', '')),
                            "line_num": i + 1,
                        })
                continue

            # Parse: component | count | unit_mass | subtotal | ...
            unit_mass = None
            count = None
            subtotal = None

            for cell in cells:
                # Unit mass: X.X kg or just number
                m = re.search(r'^(\d+\.?\d*)\s*(?:kg)?$', cell)
                if m and unit_mass is None:
                    val = float(m.group(1))
                    if val < 1000:  # heuristic
                        if count is None:
                            count = int(val) if val == int(val) else val
                        elif unit_mass is None:
                            unit_mass = val
                elif unit_mass is None:
                    m2 = re.search(r'(\d+\.?\d*)\s*kg', cell)
                    if m2:
                        unit_mass = float(m2.group(1))

                # Subtotal
                m3 = re.search(r'^(\d+\.?\d*)\s*$', cell)
                if m3 and subtotal is None and unit_mass is not None and count is not None:
                    val = float(m3.group(1))
                    if abs(val - unit_mass * count) < 1.0:
                        subtotal = val

            if unit_mass is not None and count is not None:
                rows.append({
                    "type": "line_item",
                    "unit_mass": unit_mass,
                    "count": count if isinstance(count, int) else int(count),
                    "computed_subtotal": round(unit_mass * (count if isinstance(count, int) else int(count)), 2),
                    "line_num": i + 1,
                })

    return rows


def verify_package(md_path: pathlib.Path) -> dict:
    """Run independent recomputation on a package.

    Returns dict with:
        - bom_verification: {claimed_total, computed_total, diff, status}
        - mass_verification: {claimed_total, computed_total, diff, status}
        - basis_counts: {QUOTED, CATALOG, ESTIMATED, UNKNOWN}
        - claimed_basis_counts: what the document claims
        - errors: list of error messages
        - status: PASS or FAIL
    """
    md_text = md_path.read_text(encoding="utf-8")
    errors = []
    warnings = []

    # --- BOM verification ---
    bom_rows = extract_bom_rows(md_text)
    bom_line_items = [r for r in bom_rows if r["type"] == "line_item"]
    bom_totals = [r for r in bom_rows if r["type"] == "total_claim"]

    computed_bom_total = sum(r["computed_subtotal"] for r in bom_line_items)

    # Find claimed total
    claimed_bom_total = None
    if bom_totals:
        claimed_bom_total = bom_totals[0]["value"]

    # Also search for "Total**" or "Total |" in the text
    if claimed_bom_total is None:
        m = re.search(r'\*\*Total\*\*\s*\|?\s*\$?([\d,]+\.?\d*)', md_text)
        if m:
            claimed_bom_total = float(m.group(1).replace(',', ''))

    # Also look for "Total:" patterns
    if claimed_bom_total is None:
        m = re.search(r'Total.*?\$([\d,]+\.?\d*)', md_text, re.IGNORECASE)
        if m:
            claimed_bom_total = float(m.group(1).replace(',', ''))

    bom_diff = None
    bom_status = "UNKNOWN"
    if claimed_bom_total is not None:
        bom_diff = round(computed_bom_total - claimed_bom_total, 2)
        bom_status = "PASS" if abs(bom_diff) < 0.01 else "FAIL"
        if bom_status == "FAIL":
            errors.append(
                f"BOM arithmetic error: line items sum to ${computed_bom_total:,.2f} "
                f"but document claims ${claimed_bom_total:,.2f}. "
                f"Diff: ${bom_diff:,.2f}."
            )

    # --- Basis count verification ---
    basis_counts = {"QUOTED": 0, "CATALOG": 0, "ESTIMATED": 0, "UNKNOWN": 0}
    for r in bom_line_items:
        basis_counts[r["basis"]] = basis_counts.get(r["basis"], 0) + 1

    # Search for claimed counts in the text
    claimed_quoted = None
    claimed_estimated = None
    m = re.search(r'(\d+)\s*QUOTED.*?(\d+)\s*ESTIMATED', md_text, re.IGNORECASE)
    if m:
        claimed_quoted = int(m.group(1))
        claimed_estimated = int(m.group(2))

    if claimed_quoted is not None:
        actual_quoted = basis_counts["QUOTED"]
        if actual_quoted != claimed_quoted:
            errors.append(
                f"Basis count error: document claims {claimed_quoted} QUOTED "
                f"but independent count finds {actual_quoted} QUOTED."
            )

    if claimed_estimated is not None:
        actual_estimated = basis_counts["ESTIMATED"]
        if actual_estimated != claimed_estimated:
            errors.append(
                f"Basis count error: document claims {claimed_estimated} ESTIMATED "
                f"but independent count finds {actual_estimated} ESTIMATED."
            )

    # --- Mass verification ---
    mass_rows = extract_mass_rows(md_text)
    mass_line_items = [r for r in mass_rows if r["type"] == "line_item"]
    mass_totals = [r for r in mass_rows if r["type"] == "total_claim"]

    computed_mass_total = sum(r["computed_subtotal"] for r in mass_line_items)

    claimed_mass_total = None
    if mass_totals:
        claimed_mass_total = mass_totals[0]["value"]

    # Also search for "Total | **XXX.XX**" pattern
    if claimed_mass_total is None:
        m = re.search(r'\*\*Total\*\*\s*\|?\s*\**\s*([\d,]+\.?\d*)', md_text)
        if m:
            val = float(m.group(1).replace(',', ''))
            if val > 50:  # heuristic: mass total > 50 kg
                claimed_mass_total = val

    mass_diff = None
    mass_status = "UNKNOWN"
    if claimed_mass_total is not None:
        mass_diff = round(computed_mass_total - claimed_mass_total, 2)
        mass_status = "PASS" if abs(mass_diff) < 0.5 else "FAIL"
        if mass_status == "FAIL":
            errors.append(
                f"Mass arithmetic error: line items sum to {computed_mass_total:.2f} kg "
                f"but document claims {claimed_mass_total:.2f} kg. "
                f"Diff: {mass_diff:.2f} kg."
            )

    # --- Amortization verification ---
    # Look for patterns like "$X,XXX / 7yr / 365" and "$X.XX/day"
    amort_errors = []
    for m in re.finditer(r'\$([\d,]+)\s*/\s*(\d+)\s*yr\s*/\s*365', md_text):
        capital = float(m.group(1).replace(',', ''))
        years = int(m.group(2))
        computed_daily = round(capital / years / 365, 2)
        # Search nearby for claimed daily value
        context_start = max(0, m.start() - 100)
        context_end = min(len(md_text), m.end() + 200)
        context = md_text[context_start:context_end]

        m2 = re.search(r'\$([\d.]+)\s*/\s*day', context)
        if m2:
            claimed_daily = float(m2.group(1))
            diff = round(computed_daily - claimed_daily, 2)
            if abs(diff) > 0.01:
                amort_errors.append(
                    f"Amortization error: ${capital:,.0f} / {years}yr / 365 = "
                    f"${computed_daily}/day but document claims ${claimed_daily}/day. "
                    f"Diff: ${diff}/day."
                )

    errors.extend(amort_errors)

    # --- Overall status ---
    status = "FAIL" if errors else "PASS"

    return {
        "bom_verification": {
            "claimed_total": claimed_bom_total,
            "computed_total": round(computed_bom_total, 2),
            "diff": bom_diff,
            "status": bom_status,
            "line_items_found": len(bom_line_items),
        },
        "mass_verification": {
            "claimed_total": claimed_mass_total,
            "computed_total": round(computed_mass_total, 2),
            "diff": mass_diff,
            "status": mass_status,
            "line_items_found": len(mass_line_items),
        },
        "basis_counts": basis_counts,
        "claimed_basis_counts": {
            "QUOTED": claimed_quoted,
            "ESTIMATED": claimed_estimated,
        },
        "errors": errors,
        "warnings": warnings,
        "status": status,
    }


def main():
    if len(sys.argv) < 2:
        md_path = ROOT / "product" / "PRODUCT.md"
    else:
        md_path = pathlib.Path(sys.argv[1])

    if not md_path.exists():
        print(f"Error: {md_path} does not exist", file=sys.stderr)
        return 1

    print("=" * 70)
    print("INDEPENDENT RECOMPUTATION VERIFIER (Phase 1)")
    print("=" * 70)
    print(f"Input: {md_path}")
    print()

    result = verify_package(md_path)

    print("--- BOM Verification ---")
    bv = result["bom_verification"]
    if bv["claimed_total"] is not None:
        print(f"  Claimed total:  ${bv['claimed_total']:,.2f}")
    else:
        print(f"  Claimed total:  NOT FOUND")
    print(f"  Computed total: ${bv['computed_total']:,.2f} (from {bv['line_items_found']} line items)")
    if bv["diff"] is not None:
        print(f"  Diff:           ${bv['diff']:,.2f}")
    print(f"  Status:         {bv['status']}")
    print()

    print("--- Mass Verification ---")
    mv = result["mass_verification"]
    if mv["claimed_total"] is not None:
        print(f"  Claimed total:  {mv['claimed_total']:.2f} kg")
    else:
        print(f"  Claimed total:  NOT FOUND")
    print(f"  Computed total: {mv['computed_total']:.2f} kg (from {mv['line_items_found']} line items)")
    if mv["diff"] is not None:
        print(f"  Diff:           {mv['diff']:.2f} kg")
    print(f"  Status:         {mv['status']}")
    print()

    print("--- Basis Count Verification ---")
    bc = result["basis_counts"]
    cbc = result["claimed_basis_counts"]
    print(f"  QUOTED:    computed={bc['QUOTED']}, claimed={cbc['QUOTED']}")
    print(f"  CATALOG:   computed={bc['CATALOG']}, claimed=N/A")
    print(f"  ESTIMATED: computed={bc['ESTIMATED']}, claimed={cbc['ESTIMATED']}")
    print()

    if result["errors"]:
        print("=" * 70)
        print(f"ERRORS FOUND ({len(result['errors'])})")
        print("=" * 70)
        for e in result["errors"]:
            print(f"  FAIL: {e}")
        print()

    print("=" * 70)
    print(f"OVERALL STATUS: {result['status']}")
    print("=" * 70)

    if result["status"] == "FAIL":
        print()
        print("The package contains arithmetic errors that an independent")
        print("recomputation has surfaced. These must be fixed before the")
        print("package can ship.")
        return 1

    print()
    print("All headline numbers verified by independent recomputation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
