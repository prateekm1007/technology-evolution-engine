"""
MDDG V2 — Evidence-Qualified Linkage (CTO V8 directive #2, #3, #5-8, #9, #10).

Splits SEARCH_CANDIDATE_LINK from EVIDENCE_LINK.

EVIDENCE_LINK requires auditable identifiers:
  - exact product_code match
  - K-number match
  - PMA number match
  - NCT identifier match
  - recall number match
  - MAUDE device identifier match
  - manufacturer + product_code combination
  - explicit patent citation
  - explicit paper/device identifier

SEARCH_CANDIDATE_LINK may use lexical/semantic similarity — but is NEVER evidence.

Per CTO: "A single shared word must never create an evidence edge."
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
import hashlib
import json


# =====================================================================
# LINK QUALITY TIERS
# =====================================================================

LINK_QUALITY = {
    "VERIFIED_EVIDENCE",    # exact identifier match — counts as Tier A/B evidence
    "SEARCH_CANDIDATE",     # lexical/semantic similarity only — never evidence
    "UNRESOLVED",           # no link found, explicitly recorded
}


# =====================================================================
# EVIDENCE VERIFIERS — each checks a specific identifier type
# =====================================================================

def verify_product_code_match(device_record: dict, other_record: dict) -> Optional[str]:
    """Verify that two records share the same FDA product code.

    Returns the matched product code if verified, None otherwise.
    """
    # Device product code
    device_pc = device_record.get("product_code", "")
    if not device_pc:
        return None
    # Other record may have product_code in different fields
    other_pc = (
        other_record.get("product_code") or
        other_record.get("device_report_product_code") or
        (other_record.get("device", [{}])[0].get("device_report_product_code", "")
         if other_record.get("device") and len(other_record["device"]) > 0 else "") or
        other_record.get("code_info", "")
    )
    if device_pc and other_pc and device_pc == other_pc:
        return device_pc
    return None


def verify_k_number_match(device_record: dict, other_record: dict) -> Optional[str]:
    """Verify K-number (510(k) number) match."""
    device_k = device_record.get("k_number", "")
    other_k = other_record.get("k_number", "")
    if device_k and other_k and device_k == other_k:
        return device_k
    return None


def verify_nct_id_match(device_record: dict, trial_record: dict) -> Optional[str]:
    """Verify NCT identifier match (trial linkage)."""
    # Trials have nct_id; devices may reference it in metadata
    trial_nct = trial_record.get("nct_id", "")
    device_nct = device_record.get("nct_id", "") or device_record.get("linked_nct", "")
    if trial_nct and device_nct and trial_nct == device_nct:
        return trial_nct
    return None


def verify_recall_number_match(device_record: dict, recall_record: dict) -> Optional[str]:
    """Verify recall number match."""
    device_recall = device_record.get("recall_number", "")
    recall_num = recall_record.get("recall_number", "")
    if device_recall and recall_num and device_recall == recall_num:
        return recall_num
    return None


def verify_manufacturer_product_code(device_record: dict, other_record: dict) -> Optional[str]:
    """Verify manufacturer + product_code combination match.

    This is stronger than either field alone — it requires BOTH to match.
    """
    device_mfr = (device_record.get("applicant", "") or device_record.get("manufacturer", "") or "").lower().strip()
    device_pc = device_record.get("product_code", "")
    other_mfr = (
        other_record.get("applicant", "") or
        other_record.get("manufacturer_d_name", "") or
        other_record.get("recalling_firm", "") or
        (other_record.get("device", [{}])[0].get("manufacturer_d_name", "")
         if other_record.get("device") and len(other_record["device"]) > 0 else "") or
        ""
    ).lower().strip()
    other_pc = (
        other_record.get("product_code") or
        other_record.get("device_report_product_code") or
        (other_record.get("device", [{}])[0].get("device_report_product_code", "")
         if other_record.get("device") and len(other_record["device"]) > 0 else "") or
        other_record.get("code_info", "")
    )
    # Both manufacturer AND product code must match
    if (device_mfr and other_mfr and device_pc and other_pc and
        device_mfr == other_mfr and device_pc == other_pc):
        return f"{device_mfr}:{device_pc}"
    return None


def verify_explicit_identifier(device_record: dict, other_record: dict) -> Optional[str]:
    """Check if the other record explicitly contains the device's identifier
    in its text (e.g., a paper mentioning "K123456" or a patent citing a 510(k) number).
    """
    import re
    device_k = device_record.get("k_number", "")
    device_pc = device_record.get("product_code", "")
    # Search for K-number pattern in other record's text
    other_text = " ".join(str(v) for v in other_record.values() if isinstance(v, (str, int, float)))
    if device_k and device_k in other_text:
        return f"k_number:{device_k}"
    # Search for product code as a standalone token (not substring)
    if device_pc and len(device_pc) >= 3:
        # Use word boundary to avoid false matches like "DXY" in "DXYGEN"
        pattern = r'\b' + re.escape(device_pc) + r'\b'
        if re.search(pattern, other_text):
            return f"product_code:{device_pc}"
    return None


# =====================================================================
# LINK VERIFICATION — the canonical procedure
# =====================================================================

@dataclass(frozen=True)
class VerifiedLink:
    """A verified evidence link between two records.

    quality = VERIFIED_EVIDENCE only if an auditable identifier matched.
    quality = SEARCH_CANDIDATE if only lexical/semantic similarity exists.
    quality = UNRESOLVED if no link found.
    """
    source_id: str
    target_id: str
    link_type: str              # DEVICE_HAS_RECALL, DEVICE_HAS_TRIAL, etc.
    quality: str                # LINK_QUALITY
    verification_method: str    # "product_code_match" | "k_number_match" | etc.
    verified_identifier: str    # the actual identifier that matched (or "")
    provenance: str             # source of the verification
    notes: str = ""

    def __post_init__(self):
        if self.quality not in LINK_QUALITY:
            raise ValueError(f"Bad link quality: {self.quality!r}")

    def is_evidence(self) -> bool:
        """Only VERIFIED_EVIDENCE counts as evidence."""
        return self.quality == "VERIFIED_EVIDENCE"

    def canonical_dict(self) -> dict:
        return asdict(self)


def verify_device_recall_link(device_record: dict, recall_record: dict) -> VerifiedLink:
    """Verify a device↔recall link using auditable identifiers.

    Per CTO directive #6: use product_code, UDI, recall_number, manufacturer+product.
    If no reliable identifier: LINK_STATUS = UNKNOWN, not a false link.
    """
    device_id = device_record.get("record_id", device_record.get("k_number", "unknown"))
    recall_id = recall_record.get("record_id", recall_record.get("recall_number", "unknown"))
    # Try each verification method in priority order
    for verifier, method in [
        (verify_recall_number_match, "recall_number_match"),
        (verify_product_code_match, "product_code_match"),
        (verify_manufacturer_product_code, "manufacturer_product_code_match"),
        (verify_explicit_identifier, "explicit_identifier_in_text"),
    ]:
        result = verifier(device_record, recall_record)
        if result:
            return VerifiedLink(
                source_id=device_id, target_id=recall_id,
                link_type="DEVICE_HAS_RECALL",
                quality="VERIFIED_EVIDENCE",
                verification_method=method,
                verified_identifier=result,
                provenance="src:fda_510k + src:fda_recalls",
                notes=f"verified via {method}: {result}",
            )
    # No identifier match — this is UNRESOLVED, not a search candidate
    return VerifiedLink(
        source_id=device_id, target_id=recall_id,
        link_type="DEVICE_HAS_RECALL",
        quality="UNRESOLVED",
        verification_method="none",
        verified_identifier="",
        provenance="",
        notes="RECALL_IDENTIFIER_MISSING — no auditable identifier matched",
    )


def verify_device_trial_link(device_record: dict, trial_record: dict) -> VerifiedLink:
    """Verify a device↔trial link using auditable identifiers.

    Per CTO directive #5: use explicit device identifier, NCT, manufacturer+device.
    """
    device_id = device_record.get("record_id", device_record.get("k_number", "unknown"))
    trial_id = trial_record.get("record_id", trial_record.get("nct_id", "unknown"))
    for verifier, method in [
        (verify_nct_id_match, "nct_id_match"),
        (verify_explicit_identifier, "explicit_identifier_in_text"),
        (verify_manufacturer_product_code, "manufacturer_product_code_match"),
    ]:
        result = verifier(device_record, trial_record)
        if result:
            return VerifiedLink(
                source_id=device_id, target_id=trial_id,
                link_type="DEVICE_HAS_TRIAL",
                quality="VERIFIED_EVIDENCE",
                verification_method=method,
                verified_identifier=result,
                provenance="src:fda_510k + src:ct_gov",
                notes=f"verified via {method}: {result}",
            )
    return VerifiedLink(
        source_id=device_id, target_id=trial_id,
        link_type="DEVICE_HAS_TRIAL",
        quality="UNRESOLVED",
        verification_method="none",
        verified_identifier="",
        provenance="",
        notes="TRIAL_IDENTIFIER_MISSING — no auditable identifier matched",
    )


def verify_device_paper_link(device_record: dict, paper_record: dict) -> VerifiedLink:
    """Verify a device↔paper link.

    Per CTO directive #7: accept device name explicitly mentioned, manufacturer+product,
    regulatory identifier cited, clinical-trial identifier linking both.
    """
    device_id = device_record.get("record_id", device_record.get("k_number", "unknown"))
    paper_id = paper_record.get("record_id", paper_record.get("work_id", "unknown"))
    # Check if the paper explicitly mentions the device's K-number or product code
    result = verify_explicit_identifier(device_record, paper_record)
    if result:
        return VerifiedLink(
            source_id=device_id, target_id=paper_id,
            link_type="PAPER_DESCRIBES_DEVICE",
            quality="VERIFIED_EVIDENCE",
            verification_method="explicit_identifier_in_text",
            verified_identifier=result,
            provenance="src:openalex",
            notes=f"paper explicitly mentions device identifier: {result}",
        )
    # Check if paper mentions device name + manufacturer together
    device_name = (device_record.get("device_name", "") or "").lower()
    device_mfr = (device_record.get("applicant", "") or "").lower()
    paper_text = ((paper_record.get("title", "") or "") + " " +
                  (paper_record.get("abstract", "") or "")).lower()
    if (device_name and len(device_name) > 10 and device_name in paper_text and
        device_mfr and len(device_mfr) > 3 and device_mfr in paper_text):
        return VerifiedLink(
            source_id=device_id, target_id=paper_id,
            link_type="PAPER_DESCRIBES_DEVICE",
            quality="VERIFIED_EVIDENCE",
            verification_method="device_name_plus_manufacturer_in_text",
            verified_identifier=f"{device_name}+{device_mfr}",
            provenance="src:openalex",
            notes="paper explicitly mentions device name AND manufacturer",
        )
    return VerifiedLink(
        source_id=device_id, target_id=paper_id,
        link_type="PAPER_DESCRIBES_DEVICE",
        quality="UNRESOLVED",
        verification_method="none",
        verified_identifier="",
        provenance="",
        notes="PAPER_DEVICE_IDENTIFIER_MISSING",
    )


def verify_device_patent_link(device_record: dict, patent_record: dict) -> VerifiedLink:
    """Verify a device↔patent link.

    Per CTO directive #8: accept when patent explicitly names device/manufacturer,
    or has authoritative priority/application relationship.
    """
    device_id = device_record.get("record_id", device_record.get("k_number", "unknown"))
    patent_id = patent_record.get("record_id", patent_record.get("patent_id", "unknown"))
    # Check if patent explicitly mentions device K-number or product code
    result = verify_explicit_identifier(device_record, patent_record)
    if result:
        return VerifiedLink(
            source_id=device_id, target_id=patent_id,
            link_type="PATENT_CLAIMS_DEVICE",
            quality="VERIFIED_EVIDENCE",
            verification_method="explicit_identifier_in_text",
            verified_identifier=result,
            provenance="src:huggingface_patents",
            notes=f"patent explicitly mentions device identifier: {result}",
        )
    return VerifiedLink(
        source_id=device_id, target_id=patent_id,
        link_type="PATENT_CLAIMS_DEVICE",
        quality="UNRESOLVED",
        verification_method="none",
        verified_identifier="",
        provenance="",
        notes="PATENT_DEVICE_IDENTIFIER_MISSING",
    )


def verify_device_adverse_event_link(device_record: dict, ae_record: dict) -> VerifiedLink:
    """Verify a device↔adverse_event link using product code or manufacturer."""
    device_id = device_record.get("record_id", device_record.get("k_number", "unknown"))
    ae_id = ae_record.get("record_id", ae_record.get("mdr_report_key", "unknown"))
    for verifier, method in [
        (verify_product_code_match, "product_code_match"),
        (verify_manufacturer_product_code, "manufacturer_product_code_match"),
        (verify_explicit_identifier, "explicit_identifier_in_text"),
    ]:
        result = verifier(device_record, ae_record)
        if result:
            return VerifiedLink(
                source_id=device_id, target_id=ae_id,
                link_type="DEVICE_HAS_ADVERSE_EVENT",
                quality="VERIFIED_EVIDENCE",
                verification_method=method,
                verified_identifier=result,
                provenance="src:fda_510k + src:fda_maude",
                notes=f"verified via {method}: {result}",
            )
    return VerifiedLink(
        source_id=device_id, target_id=ae_id,
        link_type="DEVICE_HAS_ADVERSE_EVENT",
        quality="UNRESOLVED",
        verification_method="none",
        verified_identifier="",
        provenance="",
        notes="AE_IDENTIFIER_MISSING",
    )


# =====================================================================
# SEARCH CANDIDATE (lexical/semantic — never evidence)
# =====================================================================

def make_search_candidate(source_id: str, target_id: str, link_type: str,
                           similarity_score: float, method: str,
                           notes: str = "") -> VerifiedLink:
    """Create a SEARCH_CANDIDATE link. This is NEVER evidence.

    Per CTO: "A discovery link can use name similarity, lexical overlap,
    embedding similarity, temporal proximity. An evidence link requires
    an auditable identifier or explicit source statement."
    """
    return VerifiedLink(
        source_id=source_id, target_id=target_id,
        link_type=link_type,
        quality="SEARCH_CANDIDATE",
        verification_method=method,
        verified_identifier="",
        provenance="",
        notes=f"search candidate (score={similarity_score:.3f}): {notes}",
    )


# =====================================================================
# HELD-OUT LINKAGE BENCHMARK (directive #17)
# =====================================================================

@dataclass
class LinkageBenchmarkPair:
    """A held-out pair for linkage precision testing."""
    pair_id: str
    link_type: str          # DEVICE_HAS_RECALL, etc.
    device_record: dict
    other_record: dict
    true_label: str         # TRUE_LINK | FALSE_LINK | UNKNOWN
    predicted_quality: str = ""  # filled by the linkage engine
    predicted_correctly: bool = False

    def canonical_dict(self) -> dict:
        return asdict(self)


def evaluate_linkage_precision(pairs: list[LinkageBenchmarkPair]) -> dict:
    """Evaluate precision of the verified-linkage engine against held-out labels.

    Per CTO directive #17: "The first goal is precision, not recall."
    """
    true_positives = 0   # TRUE_LINK predicted as VERIFIED_EVIDENCE
    false_positives = 0  # FALSE_LINK predicted as VERIFIED_EVIDENCE
    true_negatives = 0   # FALSE_LINK predicted as UNRESOLVED
    false_negatives = 0  # TRUE_LINK predicted as UNRESOLVED
    unknown_count = 0    # UNKNOWN label

    for pair in pairs:
        if pair.true_label == "UNKNOWN":
            unknown_count += 1
            continue
        if pair.predicted_quality == "VERIFIED_EVIDENCE":
            if pair.true_label == "TRUE_LINK":
                true_positives += 1
                pair.predicted_correctly = True
            else:
                false_positives += 1
                pair.predicted_correctly = False
        else:  # UNRESOLVED or SEARCH_CANDIDATE
            if pair.true_label == "FALSE_LINK":
                true_negatives += 1
                pair.predicted_correctly = True
            else:
                false_negatives += 1
                pair.predicted_correctly = False

    precision = true_positives / max(true_positives + false_positives, 1)
    recall = true_positives / max(true_positives + false_negatives, 1)
    false_link_rate = false_positives / max(true_positives + false_positives, 1)
    accuracy = (true_positives + true_negatives) / max(len([p for p in pairs if p.true_label != "UNKNOWN"]), 1)

    return {
        "total_pairs": len(pairs),
        "labeled_pairs": len([p for p in pairs if p.true_label != "UNKNOWN"]),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "true_negatives": true_negatives,
        "false_negatives": false_negatives,
        "unknown_count": unknown_count,
        "precision": precision,
        "recall": recall,
        "false_link_rate": false_link_rate,
        "accuracy": accuracy,
        "precision_gate_pass": precision >= 0.95 and false_link_rate <= 0.05,
    }
