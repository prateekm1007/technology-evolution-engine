# Cross-Corpus Science × Patent Discovery Graph — Preregistration (Issue #4)

**Status:** PILOT INFRASTRUCTURE COMPLETE. REAL_DATA_SEAL = FALSE.
**PSCD-1:** FROZEN. NOT TOUCHED.
**A2:** NOT AUTHORIZED.
**North Star:** UNPROVEN.

---

## 1. Objective

Build a unified evidence graph combining scientific papers and patent
families, then search for **cross-corpus intersection motifs** that represent
latent discovery opportunities — configurations that are *not entailed* by
the frozen evidence, are *falsifiable*, and are *sealed before outcome*.

The pilot does NOT claim discovery. It builds the instrument, the controls,
and the forensic chain. A discovery claim requires:

1. Real data (OpenAlex + EPO), not synthetic fixtures.
2. Cross-corpus candidate count beating all four null controls by ≥1.5×.
3. Retrieval-negative attestation (deterministic, per-source).
4. Sealed predictions with outcome verification in a real prediction window.
5. Independent human-expert adjudication of any confirmed candidate.

---

## 2. Architecture

```
papers (OpenAlex)  +  patents (EPO-OPS)  +  families (DOCDB)
         |                   |                   |
         v                   v                   v
      ingest.py          ingest.py         family_normalizer.py
         |                   |                   |
         +-------------------+-------------------+
                             |
                        EvidenceGraph
                     (typed nodes, provenance-
                      qualified edges, time-
                      anchored subgraphs)
                             |
                    10 motif detectors
                             |
                    Candidate list
                             |
                retrieval_negative_attestation
                  (deterministic, per-source)
                             |
                    PredictionFreeze (sealed)
                             |
                    OutcomeRelease (future)
                             |
                    deterministic scoring
                             |
                4 null controls (A/B/C/D)
                             |
                    forensic hash chain
                             |
                    ResultPackage (immutable)
                             |
                    forensic_audit (6 checks)
```

---

## 3. The 10 Intersection Motifs

| # | Motif | Structure | Prediction |
|---|-------|-----------|------------|
| M01 | Constraint Release | old paper (constraint) + patent (X-cites) + newer paper (drops constraint) | future patent claims the relaxed config |
| M02 | Paper→Patent Gap | paper reports (mech, mat) in a cell with patent activity but no later patent claims that mat | future patent claims (mech, mat) |
| M03 | Patent→Science Gap | patent claims (mech, mat) in a cell with paper activity but no later paper addresses that mat | future paper addresses (mech, mat) |
| M04 | Paper Failure → Patent Workaround | paper reports failure + later patent claims same cell without citing failure | future paper replicates or refutes workaround |
| M05 | Old Science → Enabling Patent | foundational paper (>5yr) + enabling patent (no cite) | follow-on patent extends to new material |
| M06 | Two Papers + Two Families | 2 papers in different domains on same mech + 2 families, no cross-cites | future document combines both configs |
| M07 | Three Papers + One Patent | 3 independent papers on same mech (different mats) + 1 patent (4th mat) | future doc reports 5th material |
| M08 | One Paper + Three Families | 1 paper + 3 families with different material variants | future paper identifies design rule |
| M09 | Jurisdictional Divergence | family granted in A (many claims) but limited in B (few claims) | future paper explains divergence |
| M10 | Unexplained Bridge | paper + patent in different domains sharing mech+mat, no citation | future doc cites both |

---

## 4. Provenance Semantics (EPO Citation Roles)

| Role | Meaning | Qualifies as evidence? |
|------|---------|----------------------|
| X | novelty-killing (examiner asserts target anticipates claim) | YES |
| Y | inventive-step (examiner combines targets to deny inventive step) | YES |
| A | background / state of the art | NO (context only) |
| T | theoretical / post-priority explanatory | NO |
| D | applicant-asserted (cited by applicant in application) | YES |
| * | unclassified | NO (UNKNOWN never counts) |

NPL (non-patent literature) citations — patents citing scientific papers —
are first-class edges. EPO statistics: NPL appears in ~27.8% of search reports
(>50% in chemistry/biotech).

---

## 5. Temporal Controls

- **Cutoff:** previous complete UTC day at pilot freeze time (conservative).
- **Strict <:** a document dated on or after the cutoff is NOT eligible evidence.
- **Patent evidence date:** min(priority_date, publication_date) — conservative
  (favors eligibility for prior-art purposes).
- **Prediction window:** [cutoff, cutoff + prediction_window_days]. Outcome
  verification may only use documents in this window.
- **Leakage check:** every document's date must be strictly before cutoff.
  Any violation aborts the pilot (state → ABORTED).

---

## 6. Four Null Controls

| Null | What it breaks | Expected effect |
|------|---------------|-----------------|
| NULL_A | Temporal order (shuffle all dates) | Motifs that rely on time-ordering fire at random rates |
| NULL_B | Corpus labels (swap paper↔patent on 50% of cross edges) | Motifs insensitive to corpus distinction fire identically |
| NULL_C | Citation semantics (rewire edges, preserve degree) | Motifs driven by degree artifacts fire identically |
| NULL_D | Single-corpus only (papers-only, patents-only separately) | Cross-corpus value = real_run − max(D_papers, D_patents) |

---

## 7. Decision Rule (AINT-1-equivalent)

```
cross_corpus_pass = (real_run.retrieval_negative_count > 0)
                    AND (real_run.candidate_count >= 1.5 × max(null_A, null_B, null_C, null_D_papers, null_D_patents))
                    AND forensic_chain_intact
                    AND real_data_seal == False   # honest labeling

if cross_corpus_pass:
    decision = STRUCTURAL_PASS
else:
    decision = STRUCTURAL_FAIL

is_scientific_result = False   # ALWAYS False on synthetic fixtures
```

**Kill switch:** if the cross-corpus run does NOT beat all nulls by ≥1.5×,
the architecture is RETIRED (no discovery claim is made). This mirrors
PSCD-1's AINT-1: `if A2-A1 ≤ 0 → FABRIC_STATUS = RETIRED`.

---

## 8. Forensic Integrity

- **Hash chain:** each candidate's `chain_hash` depends on the previous
  candidate's `chain_hash`. Mutating any candidate invalidates all later.
- **Result package:** immutable JSON blob with SHA-256 sidecar. Tampering
  with the file invalidates the hash.
- **Prediction freeze:** `freeze.json` + `freeze.json.sha256`. Tampering
  invalidates scoring.
- **6 forensic checks:**
  1. RESULT_PACKAGE_INTACT (hash match)
  2. REAL_DATA_SEAL_HONEST (must be False on synthetic)
  3. NOT_CLAIMED_AS_SCIENTIFIC (must be False on synthetic)
  4. CHAIN_ROOT_HASH_PRESENT (64-char SHA-256 or "EMPTY")
  5. DECISION_IN_VOCABULARY (STRUCTURAL_PASS or STRUCTURAL_FAIL)
  6. ALL_NULL_CONTROLS_PRESENT (all 5 null counts exist)

---

## 9. Orchestrator State Machine (fail-closed)

```
BLOCKED → GRAPH_LOADED → CONTROLS_VERIFIED → MOTIFS_RUN →
CANDIDATES_FILTERED → PREDICTIONS_SEALED → SCORED →
ANALYZED → DECISION_SEALED
                ↓ (any failure)
             ABORTED
```

No state may be skipped. Each transition requires the previous state's
artifacts to be present and verified.

---

## 10. What This Pilot Does NOT Do

- Does NOT modify frozen PSCD-1 artifacts.
- Does NOT authorize A2.
- Does NOT claim scientific discovery (is_scientific_result = False).
- Does NOT use real OpenAlex/EPO data (REAL_DATA_SEAL = False).
- Does NOT assume the graph wins — it must compete against A0/A1 and
  single-corpus controls (NULL_D) before any discovery claim.
- Does NOT use LLM judges for scoring (deterministic only).

---

## 11. Honest Boundary

| Item | Status |
|------|--------|
| Pilot infrastructure | COMPLETE |
| 10 motif detectors | COMPLETE (all fire on planted instances) |
| 4 null controls | COMPLETE (all run) |
| Forensic hash chain | COMPLETE (tamper-detected) |
| 33 negative tests | 33/33 PASS |
| REAL_DATA_SEAL | FALSE (synthetic fixtures) |
| is_scientific_result | FALSE (always, on synthetic) |
| Decision on synthetic data | STRUCTURAL_FAIL (honest: synthetic has no real signal) |
| PSCD-1 frozen | YES (not touched) |
| A2 authorized | NO |

**The only path to a scientific result:**
1. Ingest real OpenAlex (500 papers) + EPO-OPS (500 families) data.
2. Issue REAL_DATA_SEAL via external custodian.
3. Run the pilot on real data.
4. If STRUCTURAL_PASS: seal predictions, wait for prediction window,
   verify outcomes deterministically.
5. Independent human-expert adjudication of any confirmed candidate.

---

## 12. File Manifest

```
cross_corpus/
  __init__.py
  schema.py                  # Paper, Patent, PatentFamily, Citation, Claim, Candidate
  provenance.py              # EPO X/Y/A/T/D semantics, NPL handling
  family_normalizer.py       # DOCDB simple-family normalization
  ingest.py                  # OpenAlex + EPO-OPS JSONL ingest, per-record hashing
  graph.py                   # EvidenceGraph, time-anchored subgraphs
  temporal_controls.py       # cutoff, leakage check, prediction window
  entailed.py                # deterministic per-source not-entailed check
  candidate.py               # PredictionFreeze, OutcomeRelease, scoring
  null_controls.py           # 4 nulls (A/B/C/D)
  forensic.py                # hash chain, tamper detection, 6-check audit
  orchestrator.py            # fail-closed state machine, decision rule
  run_pilot.py               # CLI entrypoint
  motifs/
    base.py
    m01_constraint_release.py
    m02_paper_patent_gap.py
    m03_patent_science_gap.py
    m04_paper_failure_patent_workaround.py
    m05_old_science_new_patent.py
    m06_two_papers_two_families.py
    m07_three_papers_one_patent.py
    m08_one_paper_three_families.py
    m09_jurisdictional_divergence.py
    m10_unexplained_bridge.py
  fixtures/
    generate_fixtures.py     # 546 papers + 516 families, planted motifs
    papers.jsonl
    patents.jsonl
  tests/
    test_pilot.py            # 33 negative-test-style tests
  sealed_predictions/
    freeze.json              # hash-sealed candidate freeze
    freeze.json.sha256
  reports/
    cc_pilot_result.json     # immutable result package
    cc_pilot_result.json.sha256
```
