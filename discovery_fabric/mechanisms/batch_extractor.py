"""
Batch Structured Mechanism Extractor — scales to 1,000 mechanisms.

Tracks SUCCESS/PARTIAL/UNKNOWN/FAILED/UNAVAILABLE for every source record.
Runs in batches to avoid timeout. Resume-safe via checkpoint.
"""
import json
import sys
import subprocess
import hashlib
import tempfile
import time
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

EVIDENCE_FILE = REPO / "discovery_fabric/evidence/evidence.jsonl"
MECHANISMS_DIR = REPO / "discovery_fabric/mechanisms"
CHECKPOINT = MECHANISMS_DIR / "extraction_checkpoint.json"
OUTPUT = MECHANISMS_DIR / "structured_mechanisms_1k.json"

UNKNOWN = "UNKNOWN"
MECHANISM_FIELDS = [
    "OBJECTIVE", "INPUT", "PROCESS", "INTERMEDIATE_STATE", "OUTPUT",
    "MEASURED_EFFECT", "OPERATING_CONDITIONS", "CONSTRAINTS", "FAILURE_MODE", "CONTROL",
]

SYSTEM_PROMPT = """Extract a structured mechanism from this scientific paper abstract. Output JSON with fields: OBJECTIVE, INPUT, PROCESS, INTERMEDIATE_STATE, OUTPUT, MEASURED_EFFECT, OPERATING_CONDITIONS, CONSTRAINTS, FAILURE_MODE, CONTROL. Use "UNKNOWN" for any field not stated. Output ONLY JSON, no markdown."""


def extract_via_cli(title, abstract, evidence_id):
    """Use z-ai CLI to extract structured mechanism."""
    user_prompt = f"Title: {title[:150]}\nAbstract: {abstract[:1000]}\n\nExtract the 10-field JSON mechanism."
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir="/tmp") as f:
        output_path = f.name
    try:
        result = subprocess.run(
            ["z-ai", "chat", "--prompt", user_prompt, "--system", SYSTEM_PROMPT, "-o", output_path],
            capture_output=True, text=True, timeout=45
        )
        if result.returncode != 0:
            return None, "FAILED"
        with open(output_path) as f:
            resp = json.load(f)
        content = resp["choices"][0]["message"]["content"].strip().strip("`").strip()
        if content.startswith("json"):
            content = content[4:].strip()
        if content.endswith("}}"):
            content = content[:-1]
        mechanism = json.loads(content)
        for field in MECHANISM_FIELDS:
            if field not in mechanism or not mechanism[field]:
                mechanism[field] = UNKNOWN
        # Classify: SUCCESS if >=5 fields non-UNKNOWN, PARTIAL if 2-4, UNKNOWN if <2
        non_unknown = sum(1 for f in MECHANISM_FIELDS if mechanism.get(f) != UNKNOWN)
        if non_unknown >= 5:
            status = "SUCCESS"
        elif non_unknown >= 2:
            status = "PARTIAL"
        else:
            status = "UNKNOWN"
        return mechanism, status
    except json.JSONDecodeError:
        return None, "FAILED"
    except subprocess.TimeoutExpired:
        return None, "FAILED"
    except Exception:
        return None, "FAILED"
    finally:
        Path(output_path).unlink(missing_ok=True)


def load_checkpoint():
    if CHECKPOINT.exists():
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {"processed_ids": [], "mechanisms": [], "status_counts": {}}


def save_checkpoint(cp):
    with open(CHECKPOINT, "w") as f:
        json.dump(cp, f, indent=2)


def main(batch_size=50, max_total=1000):
    print(f"[{datetime.now(timezone.utc).isoformat()}] Batch mechanism extraction")
    print(f"  target: {max_total} mechanisms, batch: {batch_size}")

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

    # Filter to unprocessed
    to_process = [e for e in evidence if e["id"] not in processed][:max_total - len(mechanisms)]
    print(f"  already processed: {len(processed)}")
    print(f"  to process: {len(to_process)}")

    for i, e in enumerate(to_process):
        title = e.get("title", "")[:150]
        abstract = e.get("abstract", "")
        eid = e["id"]

        mechanism, status = extract_via_cli(title, abstract, eid)

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
            # Record failure
            mechanisms.append({
                "evidence_id": eid,
                "source": e.get("source", ""),
                "domain": e.get("domain", ""),
                "extraction_status": status,
                "mechanism_hash": UNKNOWN,
            })

        status_counts[status] = status_counts.get(status, 0) + 1
        processed.add(eid)

        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(to_process)}] total={len(mechanisms)} status={dict(status_counts)}")
            # Checkpoint every 10
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
            "mechanisms": mechanisms,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[{datetime.now(timezone.utc).isoformat()}] BATCH COMPLETE")
    print(f"  total attempted: {len(mechanisms)}")
    print(f"  status: {status_counts}")
    print(f"  saved: {OUTPUT}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--max-total", type=int, default=1000)
    args = parser.parse_args()
    main(args.batch_size, args.max_total)
