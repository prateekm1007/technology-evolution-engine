"""Build empty adjudication results template for 2-3 adjudicators."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
BLIND_PACKETS = REPO / "discovery_fabric/dsb_v1/adjudication/adjudication_packets_BLIND.json"
OUT_DIR = REPO / "discovery_fabric/dsb_v1/adjudication/instructions"

with open(BLIND_PACKETS) as f:
    packets = json.load(f)

template = {
    "adjudicator_id": "ADJ-001",
    "adjudicator_name": "[FILL IN]",
    "independence_statement": "[FILL IN — see §6 of ADJUDICATOR_INSTRUCTIONS.md]",
    "submitted_at": "[FILL IN ISO-8601]",
    "time_spent_minutes": 0,
    "scores": [
        {
            "packet_id": p["packet_id"],
            "Q1_MECHANISM_MATCH": "[YES|PARTIAL|NO]",
            "Q2_DISCOVERY_STRUCTURE_MATCH": "[YES|PARTIAL|NO]",
            "Q3_SPECIFICITY": "[YES|NO]",
            "comments": ""
        }
        for p in packets
    ]
}

out_path = OUT_DIR / "adjudication_results_template.json"
with open(out_path, "w") as f:
    json.dump(template, f, indent=2, ensure_ascii=False)
print(f"Template saved: {out_path}")
print(f"Packet slots: {len(template['scores'])}")
