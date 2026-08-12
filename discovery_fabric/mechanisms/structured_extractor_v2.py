"""
Structured Mechanism Extractor V2 — uses z-ai CLI for LLM calls.

Extracts 10-field structured mechanisms from evidence abstracts.
Missing fields = UNKNOWN (never fabricated).
Every element traces to source evidence.
"""
import json
import sys
import subprocess
import hashlib
import tempfile
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

EVIDENCE_FILE = REPO / "discovery_fabric/evidence/evidence.jsonl"
MECHANISMS_DIR = REPO / "discovery_fabric/mechanisms"
MECHANISMS_DIR.mkdir(parents=True, exist_ok=True)

UNKNOWN = "UNKNOWN"

MECHANISM_FIELDS = [
    "OBJECTIVE", "INPUT", "PROCESS", "INTERMEDIATE_STATE", "OUTPUT",
    "MEASURED_EFFECT", "OPERATING_CONDITIONS", "CONSTRAINTS", "FAILURE_MODE", "CONTROL",
]

SYSTEM_PROMPT = """You are a mechanism extractor for a scientific discovery engine. Extract a structured mechanism from the given scientific paper abstract.

Extract these 10 fields:
- OBJECTIVE: What problem or goal does this work address?
- INPUT: What is the starting material, system, or condition?
- PROCESS: What transformation or method is applied?
- INTERMEDIATE_STATE: What intermediate state or change occurs?
- OUTPUT: What is the resulting material, system, or state?
- MEASURED_EFFECT: What quantitative or qualitative effect is measured?
- OPERATING_CONDITIONS: Under what conditions does this operate?
- CONSTRAINTS: What limits or constrains this mechanism?
- FAILURE_MODE: Under what conditions does this fail or degrade?
- CONTROL: What control or comparison is used?

CRITICAL RULES:
1. Extract ONLY what is directly stated or clearly implied in the abstract.
2. If a field is not mentioned, output "UNKNOWN" — NEVER guess or invent.
3. Be specific — quote key terms from the abstract where possible.
4. Output ONLY valid JSON, no markdown fences.

Output format:
{"OBJECTIVE": "...", "INPUT": "...", "PROCESS": "...", "INTERMEDIATE_STATE": "...", "OUTPUT": "...", "MEASURED_EFFECT": "...", "OPERATING_CONDITIONS": "...", "CONSTRAINTS": "...", "FAILURE_MODE": "...", "CONTROL": "..."}}"""


def extract_mechanism_via_cli(title, abstract, evidence_id):
    """Use z-ai CLI to extract structured mechanism."""
    user_prompt = f"""Paper ID: {evidence_id}
Title: {title}

Abstract: {abstract[:1200]}

Extract the 10-field structured mechanism as JSON. Use "UNKNOWN" for any field not mentioned in the abstract."""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir="/tmp") as f:
        output_path = f.name

    try:
        result = subprocess.run(
            ["z-ai", "chat", "--prompt", user_prompt, "--system", SYSTEM_PROMPT, "-o", output_path],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return None, f"cli_error: {result.stderr[:100]}"

        with open(output_path) as f:
            resp = json.load(f)

        content = resp["choices"][0]["message"]["content"]
        # Strip markdown fences
        content = content.strip().strip("`").strip()
        if content.startswith("json"):
            content = content[4:].strip()
        # Remove trailing extra braces
        if content.endswith("}}"):
            content = content[:-1]

        mechanism = json.loads(content)

        # Validate all fields, fill missing with UNKNOWN
        for field in MECHANISM_FIELDS:
            if field not in mechanism or not mechanism[field]:
                mechanism[field] = UNKNOWN

        return mechanism, "success"

    except json.JSONDecodeError:
        return None, "json_parse_error"
    except subprocess.TimeoutExpired:
        return None, "timeout"
    except Exception as e:
        return None, f"error: {type(e).__name__}: {str(e)[:80]}"
    finally:
        Path(output_path).unlink(missing_ok=True)


def main(max_items=50):
    """Extract structured mechanisms from evidence with abstracts."""
    print(f"[{datetime.now(timezone.utc).isoformat()}] Structured mechanism extraction V2 (LLM via CLI)")
    print(f"  max items: {max_items}")

    # Load evidence with abstracts
    evidence_with_abstracts = []
    with open(EVIDENCE_FILE) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                abstract = e.get("abstract", "")
                if abstract and abstract != "UNAVAILABLE" and len(abstract) > 50:
                    evidence_with_abstracts.append(e)

    print(f"  evidence with usable abstracts: {len(evidence_with_abstracts)}")
    to_process = evidence_with_abstracts[:max_items]
    print(f"  processing: {len(to_process)}")

    mechanisms = []
    success = 0
    fail = 0

    for i, e in enumerate(to_process):
        title = e.get("title", "")[:200]
        abstract = e.get("abstract", "")
        eid = e["id"]

        mechanism, status = extract_mechanism_via_cli(title, abstract, eid)

        if mechanism and status == "success":
            success += 1
            mechanism["_extraction_method"] = "llm_cli"
        else:
            fail += 1
            # Minimal fallback
            mechanism = {field: UNKNOWN for field in MECHANISM_FIELDS}
            mechanism["OBJECTIVE"] = title[:200]
            mechanism["_extraction_method"] = f"failed:{status}"

        mechanism["evidence_id"] = eid
        mechanism["source"] = e.get("source", "")
        mechanism["domain"] = e.get("domain", "")
        mechanism["source_uri"] = e.get("source_uri", "")
        mechanism["extraction_timestamp"] = datetime.now(timezone.utc).isoformat()
        mechanism["mechanism_hash"] = hashlib.sha256(
            json.dumps(mechanism, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        ).hexdigest()

        mechanisms.append(mechanism)

        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(to_process)}] success={success} fail={fail}")

    # Save
    output = MECHANISMS_DIR / "structured_mechanisms_v2.json"
    with open(output, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_mechanisms": len(mechanisms),
            "llm_success": success,
            "failed": fail,
            "mechanisms": mechanisms,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[{datetime.now(timezone.utc).isoformat()}] EXTRACTION COMPLETE")
    print(f"  total: {len(mechanisms)}")
    print(f"  llm success: {success}")
    print(f"  failed: {fail}")

    # UNKNOWN rates
    unknown_rates = {}
    for field in MECHANISM_FIELDS:
        uc = sum(1 for m in mechanisms if m.get(field) == UNKNOWN)
        unknown_rates[field] = f"{uc}/{len(mechanisms)} ({100*uc/len(mechanisms):.0f}%)"
    print(f"\n  UNKNOWN rates by field:")
    for field, rate in unknown_rates.items():
        print(f"    {field}: {rate}")

    print(f"  saved: {output}")
    return mechanisms


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-items", type=int, default=50)
    args = parser.parse_args()
    main(args.max_items)
