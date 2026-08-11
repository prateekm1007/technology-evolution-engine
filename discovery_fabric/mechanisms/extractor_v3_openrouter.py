"""
Structured Mechanism Extractor V3 — uses OpenRouter (Gemma 4 26B free tier).

Scales to 1,000 mechanisms. Tracks SUCCESS/PARTIAL/UNKNOWN/FAILED/UNAVAILABLE.
Resume-safe via checkpoint. Missing fields = UNKNOWN (never fabricated).
"""
import json
import sys
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.connectors.openrouter_llm import chat_json

EVIDENCE_FILE = REPO / "discovery_fabric/evidence/evidence.jsonl"
MECHANISMS_DIR = REPO / "discovery_fabric/mechanisms"
CHECKPOINT = MECHANISMS_DIR / "extraction_checkpoint_v3.json"
OUTPUT = MECHANISMS_DIR / "structured_mechanisms_1k_v3.json"

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
{"OBJECTIVE": "...", "INPUT": "...", "PROCESS": "...", "INTERMEDIATE_STATE": "...", "OUTPUT": "...", "MEASURED_EFFECT": "...", "OPERATING_CONDITIONS": "...", "CONSTRAINTS": "...", "FAILURE_MODE": "...", "CONTROL": "..."}"""


def classify_status(mechanism):
    """Classify extraction quality."""
    non_unknown = sum(1 for f in MECHANISM_FIELDS if mechanism.get(f) != UNKNOWN)
    if non_unknown >= 5:
        return "SUCCESS"
    elif non_unknown >= 2:
        return "PARTIAL"
    else:
        return "UNKNOWN"


def extract_mechanism(title, abstract, evidence_id):
    """Extract structured mechanism via OpenRouter."""
    prompt = f"""Paper ID: {evidence_id}
Title: {title[:150]}

Abstract: {abstract[:1000]}

Extract the 10-field structured mechanism as JSON. Use "UNKNOWN" for any field not mentioned in the abstract."""

    result = chat_json(prompt, system=SYSTEM_PROMPT, max_tokens=1000)
    if not result:
        return None, "FAILED"

    # Validate all fields present, fill missing with UNKNOWN
    for field in MECHANISM_FIELDS:
        if field not in result or not result[field]:
            result[field] = UNKNOWN

    status = classify_status(result)
    return result, status


def load_checkpoint():
    if CHECKPOINT.exists():
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {"processed_ids": [], "mechanisms": [], "status_counts": {}}


def save_checkpoint(cp):
    with open(CHECKPOINT, "w") as f:
        json.dump(cp, f, indent=2)


def main(max_total=1000, batch_save=5):
    print(f"[{datetime.now(timezone.utc).isoformat()}] Mechanism extraction V3 (OpenRouter)")
    print(f"  target: {max_total} mechanisms")

    # Load evidence with abstracts
    evidence = []
    with open(EVIDENCE_FILE) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                abstract = e.get("abstract", "")
                if abstract and abstract != "UNAVAILABLE" and len(abstract) > 50:
                    evidence.append(e)
    print(f"  evidence with abstracts: {len(evidence)}")

    cp = load_checkpoint()
    processed = set(cp["processed_ids"])
    mechanisms = cp["mechanisms"]
    status_counts = cp.get("status_counts", {})

    to_process = [e for e in evidence if e["id"] not in processed][:max_total - len(mechanisms)]
    print(f"  already processed: {len(processed)}")
    print(f"  to process: {len(to_process)}")

    for i, e in enumerate(to_process):
        title = e.get("title", "")[:150]
        abstract = e.get("abstract", "")
        eid = e["id"]

        mechanism, status = extract_mechanism(title, abstract, eid)

        if mechanism:
            mechanism["evidence_id"] = eid
            mechanism["source"] = e.get("source", "")
            mechanism["domain"] = e.get("domain", "")
            mechanism["source_uri"] = e.get("source_uri", "")
            mechanism["extraction_timestamp"] = datetime.now(timezone.utc).isoformat()
            mechanism["extraction_status"] = status
            mechanism["mechanism_hash"] = hashlib.sha256(
                json.dumps(mechanism, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
            ).hexdigest()
            mechanisms.append(mechanism)
        else:
            mechanisms.append({
                "evidence_id": eid,
                "source": e.get("source", ""),
                "domain": e.get("domain", ""),
                "extraction_status": status,
                "mechanism_hash": UNKNOWN,
            })

        status_counts[status] = status_counts.get(status, 0) + 1
        processed.add(eid)

        if (i + 1) % batch_save == 0:
            print(f"  [{i+1}/{len(to_process)}] total={len(mechanisms)} status={dict(status_counts)}")
            cp["processed_ids"] = list(processed)
            cp["mechanisms"] = mechanisms
            cp["status_counts"] = status_counts
            save_checkpoint(cp)

        if len(mechanisms) >= max_total:
            break

    # Final save
    cp["processed_ids"] = list(processed)
    cp["mechanisms"] = mechanisms
    cp["status_counts"] = status_counts
    save_checkpoint(cp)

    with open(OUTPUT, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_attempted": len(mechanisms),
            "status_counts": status_counts,
            "llm_backend": "openrouter/gemma-4-26b-a4b-it:free",
            "mechanisms": mechanisms,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[{datetime.now(timezone.utc).isoformat()}] EXTRACTION COMPLETE")
    print(f"  total: {len(mechanisms)}")
    print(f"  status: {status_counts}")
    print(f"  saved: {OUTPUT}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-total", type=int, default=1000)
    args = parser.parse_args()
    main(args.max_total)
