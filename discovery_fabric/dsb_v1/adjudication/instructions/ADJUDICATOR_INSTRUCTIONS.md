# ADJUDICATOR INSTRUCTIONS — DSB V1

**Version:** 1.0
**Date:** 2026-08-12
**Status:** AWAITING 2-3 INDEPENDENT EXPERT ADJUDICATORS

---

## 1. Your Role

You are an independent expert adjudicator for the Discovery-Structure Benchmark V1 (DSB V1). Your task is to score 80 scientific-prediction packets produced by an AI system. You must NOT be:
- The experimenter who built the benchmark
- An AI/LLM proxy (we explicitly require human judgment)
- Affiliated with the engine being evaluated

You SHOULD be:
- A domain expert in at least one of: materials science, molecular biology, machine learning, immunology, or a related field
- Willing to commit 2-4 hours of focused attention
- Willing to sign an independence statement

---

## 2. What You Will See

For each of the 80 packets, you will see:

```
{
  "packet_id": "ADJ-XXXXXXXXXXXX",
  "exposed_facts": [
    "fact 1 the AI system saw",
    "fact 2 the AI system saw",
    ...
  ],
  "proposed_relationship": "the AI's proposed relationship",
  "proposed_mechanism": "the AI's proposed mechanism",
  "proposed_constraint_released": "the AI's proposed constraint release"
}
```

You will NOT see:
- Whether the case is REAL (a historical discovery) or FABRICATED (a counterfactual)
- Which of 4 arms produced the proposal (LLM-only, mechanism-only, combination, full system)
- The "correct" answer or breakthrough relationship
- Any withheld facts
- The cutoff date or historical source

This blinding is essential. Do not attempt to de-anonymize the packets.

---

## 3. Three Questions Per Packet

For each packet, answer three questions:

### Q1. MECHANISM_MATCH
**Question:** Does the proposed mechanism plausibly explain a real scientific mechanism that could underlie a discovery from these facts?

**Options:**
- `YES` — The mechanism is scientifically plausible, specific, and ties directly to the exposed facts.
- `PARTIAL` — The mechanism is plausible but generic, vague, or only loosely tied to the facts.
- `NO` — The mechanism is scientifically incorrect, incoherent, or restates the facts without explaining anything.

### Q2. DISCOVERY_STRUCTURE_MATCH
**Question:** Does the proposed_relationship express a relationship NOT explicit in the exposed_facts that combines them in a novel way?

**Options:**
- `YES` — The proposal introduces a genuinely new relationship that combines ≥2 exposed facts in a way not stated in the input.
- `PARTIAL` — The proposal introduces something not strictly explicit, but is a trivial restatement or a minor extension.
- `NO` — The proposal merely restates an exposed fact, or is too vague to constitute a relationship.

### Q3. SPECIFICITY
**Question:** Is the proposed_relationship specific enough to be falsifiable?

**Options:**
- `YES` — The proposal names specific entities, mechanisms, or outcomes that could be tested.
- `NO` — The proposal is too vague to test (e.g., "could improve performance" without specifying what improves, by how much, or how to measure).

---

## 4. Scoring Rubric (Detailed)

### Q1 MECHANISM_MATCH — Examples

**YES example:** "The proposed mechanism correctly identifies that lithium ions can intercalate into both electrodes at different potentials, enabling a rocking-chair architecture without lithium metal plating. This is a specific, physically plausible mechanism tied to the exposed facts."

**PARTIAL example:** "The proposed mechanism discusses ion transport and electrodes but doesn't specify what makes this combination work or what prevents dendrites. It's plausible but generic."

**NO example:** "The proposed mechanism simply restates that 'non-aqueous electrolytes conduct ions' without explaining anything new. Or: the mechanism is scientifically wrong (e.g., claims dendrites form in solid electrolytes when the facts say otherwise)."

### Q2 DISCOVERY_STRUCTURE_MATCH — Examples

**YES example:** Exposed facts mention (a) lithium metal dendrites are unsafe, (b) non-aqueous electrolytes conduct Li+ ions, (c) electrodes need reversible ion insertion. The proposed relationship is "Combine a Li-intercalation cathode with a Li-intercalation anode in a non-aqueous electrolyte to avoid lithium metal plating." This COMBINES facts (a)+(b)+(c) into a relationship NOT explicitly stated.

**PARTIAL example:** The proposed relationship is "Use a non-aqueous electrolyte to improve battery safety." This uses fact (b) and loosely connects to (a), but doesn't combine them into a novel relationship — it's a trivial extension.

**NO example:** The proposed relationship is "Non-aqueous electrolytes conduct lithium ions." This merely restates fact (b).

### Q3 SPECIFICITY — Examples

**YES example:** "A LiCoO2 cathode paired with a graphite anode in a non-aqueous electrolyte achieves >100 cycles without dendrite formation." Specific entities, specific outcome, testable.

**NO example:** "New battery architectures could improve safety." No specific entities, no specific outcome, not testable.

---

## 5. Critical: Watch for the Fabricated-vs-Real Pattern

The benchmark contains 40 real cases (historical discoveries that actually happened) and 40 fabricated counterfactuals (plausible-sounding proposals that did NOT happen). You do NOT know which is which.

**Be especially careful with proposals that sound highly plausible.** Some fabricated counterfactuals are designed to sound as plausible as real discoveries. Your job is to evaluate the QUALITY of the proposed relationship (mechanism + novelty + specificity), NOT whether you happen to recognize the discovery.

If you recognize a real discovery from the exposed facts, do NOT let that influence your scoring — score the QUALITY of the AI's proposal on its own merits.

---

## 6. Independence Statement

When you submit your results, you MUST include this signed statement:

```
I, [NAME], certify that:
1. I am not the experimenter who built this benchmark.
2. I am not an AI or LLM proxy.
3. I have no financial or professional conflict of interest with the engine being evaluated.
4. I scored each packet based solely on the scientific content visible in the packet.
5. I did not discuss my scores with other adjudicators before submitting.
6. I spent at least 2 hours on this task.

Signed: [NAME]
Date: [DATE]
Affiliation: [AFFILIATION]
Domain expertise: [DOMAINS]
```

---

## 7. Submission Format

Submit your results as a JSON file with this schema:

```json
{
  "adjudicator_id": "ADJ-001",
  "adjudicator_name": "[NAME]",
  "independence_statement": "[full signed statement from §6]",
  "submitted_at": "ISO-8601 timestamp",
  "time_spent_minutes": [integer],
  "scores": [
    {
      "packet_id": "ADJ-XXXXXXXXXXXX",
      "Q1_MECHANISM_MATCH": "YES|PARTIAL|NO",
      "Q2_DISCOVERY_STRUCTURE_MATCH": "YES|PARTIAL|NO",
      "Q3_SPECIFICITY": "YES|NO",
      "comments": "[optional free-text comment, max 200 chars]"
    },
    ...
  ]
}
```

Submit one file per adjudicator. Save to:
`discovery_fabric/dsb_v1/adjudication/results/adjudicator_[ID].json`

---

## 8. What Happens After You Submit

Once 2-3 adjudicators have submitted:

1. **Inter-rater agreement** will be measured (Cohen's kappa for 2 raters, Fleiss' kappa for 3+ raters).
2. **Human vs deterministic-scorer confusion matrices** will be computed separately for real and fabricated cases.
3. **Focused review** of the 12 machine "recoveries" and all cases where fabricated > real.
4. **Architecture comparison** will be recomputed using human verdicts as the gold standard.
5. **DSB V1 closure decision** based on whether scorer validity is established and the fabricated-vs-real inversion is explained.

Your work is essential to closing this benchmark. Thank you.

---

## 9. What You Need

- The blind packets file: `adjudication/adjudication_packets_BLIND.json`
- This instructions file: `adjudication/instructions/ADJUDICATOR_INSTRUCTIONS.md`
- The results template: `adjudication/instructions/adjudication_results_template.json`
- A quiet 2-4 hour block of focused time
- Domain expertise in at least one relevant field

---

**End of Adjudicator Instructions.**
