# DISCOVERY STRUCTURE ADJUDICATION RUBRIC V1

**Frozen:** 2026-08-12
**Status:** FROZEN — no revision after seeing results. Any revision becomes V2 and requires a new validation set.

---

## Purpose

This rubric defines explicit, operationalized criteria for human experts to adjudicate whether a proposed mechanism captures a historical discovery relationship. It separates four distinct constructs that must NOT be collapsed.

---

## Four Constructs

### 1. MECHANISM_RECOGNITION (MR)
**Question:** Does the proposal identify the same physical/chemical/biological mechanisms or components as the target?

**Binary:** YES / NO

**Positive example:**
- Target: "Cas9 + guide RNA = programmable DNA cleavage"
- Proposal: "RNA-guided Cas9 nuclease for genome editing"
- MR = YES: Both identify Cas9 and RNA-guided cleavage as the mechanism.

**Negative example:**
- Target: "Cas9 + guide RNA = programmable DNA cleavage"
- Proposal: "Zinc finger proteins to target specific DNA sequences"
- MR = NO: Different mechanism (zinc fingers vs Cas9).

### 2. DISCOVERY_STRUCTURE (DS)
**Question:** Does the proposal identify the same RELATIONSHIP, COMBINATION, CONSTRAINT RELEASE, or INSIGHT that makes the target a discovery — not just the same components?

**Ordinal:** 2 / 1 / 0
- 2 = FULL: Proposal captures the core discovery relationship (e.g., the combination, the inversion, the contradiction resolution)
- 1 = PARTIAL: Proposal identifies components but misses the specific relationship that constitutes the discovery
- 0 = NONE: Proposal does not capture the discovery relationship

**Positive example (DS=2):**
- Target: "LiCoO2 cathode + graphite anode = safe reversible battery (combining two intercalation mechanisms eliminates lithium metal)"
- Proposal: "Combine LiCoO2 cathode with graphite anode for reversible intercalation battery"
- DS = 2: Captures the combination relationship AND the insight (eliminating lithium metal).

**Partial example (DS=1):**
- Target: "LiCoO2 + graphite = safe reversible battery"
- Proposal: "Use LiCoO2 as a battery cathode material"
- DS = 1: Identifies a component (LiCoO2) but misses the combination relationship.

**Negative example (DS=0):**
- Target: "LiCoO2 + graphite = safe reversible battery"
- Proposal: "Use lithium metal electrodes for high energy density"
- DS = 0: Different approach entirely (lithium metal, not intercalation combination).

### 3. SCIENTIFIC_SIGNIFICANCE (SS)
**Question:** Would the proposal, if acted upon, have been sufficient to motivate the historical experiment or an equivalent one?

**Binary:** YES / NO

**Positive example:**
- Target: "Thermal cycling + Taq polymerase = exponential DNA amplification"
- Proposal: "Cycle temperature with thermostable polymerase for repeated DNA replication"
- SS = YES: This proposal would motivate building a thermal cycler with Taq.

**Negative example:**
- Target: "Thermal cycling + Taq polymerase = exponential DNA amplification"
- Proposal: "Study thermostable enzymes in bacteria"
- SS = NO: This is basic research, not a proposal that would motivate PCR.

### 4. HISTORICAL_RECONSTRUCTION (HR)
**Question:** Is the target a real historical discovery or a fabricated one? (Based on the evidence and target mechanism only, not external knowledge.)

**Binary:** REAL / FABRICATED

**Note:** Reviewers must base this judgment ONLY on the internal consistency of the evidence and target. Does the target mechanism follow logically from the pre-discovery evidence (REAL), or does it require information not present in the evidence (FABRICATED)?

---

## Adjudication Protocol

### For each case, the reviewer sees:
1. Pre-discovery evidence (what was known before)
2. Proposed mechanism (what the system proposed)
3. Target mechanism (what the discovery actually was)

### Reviewer does NOT see:
- System configuration (B/C/D/E/F)
- V3 scorer result
- Real/fabricated label
- Discovery name
- Discovery year
- Historical context beyond the evidence

### Reviewer answers:
1. MR: YES / NO
2. DS: 2 / 1 / 0
3. SS: YES / NO
4. HR: REAL / FABRICATED
5. Confidence: 0.0-1.0
6. Brief reasoning (1-2 sentences)

### Consensus rule:
- 3 reviewers per case
- Majority consensus (≥2 of 3 agree)
- If all 3 disagree on DS, use median (the middle value)
- Record all disagreements for analysis

---

## Acceptance Criteria for the Rubric

The rubric is validated only if:
1. Pairwise inter-rater agreement on DS ≥ 70% (within 1 point)
2. Pairwise inter-rater agreement on MR ≥ 80%
3. Pairwise inter-rater agreement on HR ≥ 70%
4. Majority consensus is achievable for ≥ 90% of cases

If these criteria are NOT met, the construct is insufficiently operationalized and must be redesigned before any model evaluation proceeds.

---

## Comparison to V3

After human labels are frozen:
- Compare V3 DSM to human DS consensus
- Compare V3 MM to human MR consensus
- Report agreement, false positives, false negatives
- Do NOT tune V3 based on results
- Any V3 revision becomes V4 and requires new validation

---

## Frozen

This rubric is frozen. No changes after results are seen.
Any revision = Rubric V2 = new validation set required.
