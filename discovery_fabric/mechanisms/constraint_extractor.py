"""
Constraint Extraction Layer — extracts physical/operational constraints from mechanisms.

This is the missing ingredient. Without constraints, candidates are superficial analogies.
With constraints, candidates can be tested for transferability.

Extracts:
  ENERGY_SOURCE, TIMESCALE, TEMPERATURE, PRESSURE,
  MATERIAL_REQUIREMENTS, BIOLOGICAL_REQUIREMENTS, KNOWN_LIMITATIONS
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.connectors.openrouter_llm import chat_json

MECHANISMS_FILE = REPO / "discovery_fabric/mechanisms/extraction_checkpoint_v4.json"
OUTPUT = REPO / "discovery_fabric/mechanisms/constraints_v4.json"

UNKNOWN = "UNKNOWN"

CONSTRAINT_FIELDS = [
    "ENERGY_SOURCE", "TIMESCALE", "TEMPERATURE", "PRESSURE",
    "MATERIAL_REQUIREMENTS", "BIOLOGICAL_REQUIREMENTS", "KNOWN_LIMITATIONS",
]

SYSTEM_PROMPT = """You are a constraint extractor for a scientific discovery engine. Extract physical and operational constraints from a mechanism description.

Extract these 7 fields:
- ENERGY_SOURCE: What energy drives this mechanism? (e.g., thermal, electrical, chemical, photonic, mechanical)
- TIMESCALE: What is the characteristic timescale? (e.g., nanoseconds, hours, years)
- TEMPERATURE: What temperature range is required?
- PRESSURE: What pressure range is required?
- MATERIAL_REQUIREMENTS: What material properties are needed? (e.g., conductivity, porosity, flexibility)
- BIOLOGICAL_REQUIREMENTS: What biological conditions are needed? (e.g., pH, aqueous environment, cellular machinery)
- KNOWN_LIMITATIONS: What are the known failure modes or limitations?

CRITICAL RULES:
1. Extract ONLY from the provided mechanism text and abstract.
2. Use "UNKNOWN" if not stated — NEVER guess.
3. Be specific and quantitative where possible.

Output ONLY valid JSON:
{"ENERGY_SOURCE": "...", "TIMESCALE": "...", "TEMPERATURE": "...", "PRESSURE": "...", "MATERIAL_REQUIREMENTS": "...", "BIOLOGICAL_REQUIREMENTS": "...", "KNOWN_LIMITATIONS": "..."}"""


def extract_constraints(mechanism, abstract):
    """Extract constraints from a mechanism + its source abstract."""
    # Build mechanism summary
    mech_summary = "\n".join(f"{f}: {mechanism.get(f, UNKNOWN)}" for f in [
        "OBJECTIVE", "INPUT", "PROCESS", "OUTPUT", "MEASURED_EFFECT",
        "OPERATING_CONDITIONS", "CONSTRAINTS", "FAILURE_MODE"
    ])

    prompt = f"""Mechanism:
{mech_summary}

Source abstract:
{abstract[:800]}

Extract the 7 constraint fields as JSON. Use "UNKNOWN" for any field not stated."""

    result = chat_json(prompt, system=SYSTEM_PROMPT, max_tokens=600)
    if not result:
        return None

    for field in CONSTRAINT_FIELDS:
        if field not in result or not result[field]:
            result[field] = UNKNOWN

    return result


def main(max_items=31):
    print(f"[{datetime.now(timezone.utc).isoformat()}] Constraint extraction starting")
    print(f"  target: {max_items} mechanisms")

    with open(MECHANISMS_FILE) as f:
        data = json.load(f)

    mechanisms = [m for m in data.get("mechanisms", []) if m.get("extraction_status") == "SUCCESS"]
    print(f"  SUCCESS mechanisms available: {len(mechanisms)}")

    # Load evidence for abstracts
    evidence_index = {}
    with open(REPO / "discovery_fabric/evidence/evidence.jsonl") as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                evidence_index[e["id"]] = e

    to_process = mechanisms[:max_items]
    print(f"  processing: {len(to_process)}")

    # Load existing results for resume
    existing = {}
    if OUTPUT.exists():
        with open(OUTPUT) as f:
            old = json.load(f)
            for c in old.get("constraints", []):
                eid = c.get("evidence_id", "")
                if eid:
                    existing[eid] = c

    results = []
    success = sum(1 for c in existing.values() if c.get("extraction_status") != "FAILED")

    for i, m in enumerate(to_process):
        eid = m.get("evidence_id", "")
        if eid in existing:
            results.append(existing[eid])
            continue

        e = evidence_index.get(eid, {})
        abstract = e.get("abstract", "")

        constraints = extract_constraints(m, abstract)

        if constraints:
            success += 1
            constraints["evidence_id"] = eid
            constraints["mechanism_hash"] = m.get("mechanism_hash", "")
            constraints["extraction_timestamp"] = datetime.now(timezone.utc).isoformat()
            results.append(constraints)
        else:
            results.append({
                "evidence_id": eid,
                "extraction_status": "FAILED",
            })

        # Save after every item
        with open(OUTPUT, "w") as f:
            json.dump({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total": len(results),
                "success": success,
                "constraints": results,
            }, f, indent=2, ensure_ascii=False)

        if (i + 1) % 5 == 0:
            print(f"  [{i+1}/{len(to_process)}] success={success}")

        time.sleep(0.5)

    with open(OUTPUT, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total": len(results),
            "success": success,
            "constraints": results,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[{datetime.now(timezone.utc).isoformat()}] COMPLETE")
    print(f"  total: {len(results)}, success: {success}")
    print(f"  saved: {OUTPUT}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-items", type=int, default=31)
    args = parser.parse_args()
    main(args.max_items)
