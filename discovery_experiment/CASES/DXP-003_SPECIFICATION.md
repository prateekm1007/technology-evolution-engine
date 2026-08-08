# Discovery Experiment Specification — DXP-003

**Status:** FROZEN (pre-execution)
**Date:** 2026-08-08
**Engine commit:** f8e3f2ac136e3b03acc0b3314dc901fc614ae4a8
**Predecessors:** DXP-001 (NOT DISCOVERY), DXP-002 (NOT DISCOVERY, H2 supported not confirmed)
**Purpose:** Positive-control diagnostic — distinguish generator deficit vs challenge problem vs filter problem vs LLM limitation

---

## Purpose

DXP-001 and DXP-002 both failed. H2 (generator weakness) is supported but not confirmed. DXP-003 is a **positive-control experiment**: a problem where a non-obvious, experimentally testable mechanism transfer is known to exist, but the transfer is NOT supplied to the engine.

The experiment runs ALL conditions under identical information boundaries:
- Engine (mechanism extraction → abstraction → transfer → hypotheses → adversarial)
- Generic LLM (same model, no pipeline, same prompt)
- Retrieval-only (TF-IDF/entity overlap)
- Human control (experimenter with both documents)
- Matched null (target problem only, no source mechanism)

This produces a capability ceiling:
- If engine fails but humans/LLM succeed → generator/architecture deficit
- If everyone fails → challenge problem (poorly chosen)
- If engine succeeds where controls fail → approaching North Star
- If engine produces candidates but adversarial kills them → filter problem

---

## 1. Challenge Selection

**Source domain:** Bioacoustics — bat echolocation signal processing (FM sweeps, Doppler compensation, jamming avoidance)

**Target domain:** Signal processing — adaptive waveform design for radar clutter rejection in maritime surveillance

**Why this challenge:**

1. **Known transferable mechanism exists:** Bat echolocation employs frequency-modulated (FM) sweeps with adaptive duration and bandwidth based on target distance. Bats also use Doppler-shift compensation (DSC) to maintain the echo within their hearing sensitivity range, and exhibit jamming avoidance responses (JAR) when multiple bats echolocate simultaneously. These mechanisms have documented parallels in radar waveform design — adaptive pulse duration, Doppler processing, and interference mitigation. The transfer is established in the bio-inspired radar literature but is NOT obvious from the domain descriptions alone.

2. **Not in the input:** The source document describes bat echolocation in biological terms. The target document describes the radar clutter problem in engineering terms. Neither references the other domain.

3. **Experimentally testable:** Radar waveform performance can be simulated. The prediction (e.g., "adaptive FM sweep duration based on range estimate reduces clutter false alarms by X%") can be checked against radar simulation principles.

4. **Genuine lexical distance:** Bat bioacoustics uses "laryngeal echolocation," "auditory fovea," "Doppler-shift compensation," "jamming avoidance response." Maritime radar uses "pulse compression," "range-Doppler coupling," "clutter sidelobes," "constant false alarm rate."

5. **Multiple plausible mechanisms:** The transfer has several aspects (FM sweep adaptation, Doppler compensation, jamming avoidance) that could generate competing hypotheses — testing whether the engine can produce materially different candidates.

### Expected transfer (predefined by expert, NOT in engine input)

The engine should ideally produce a transfer mapping:
- Bat's adaptive call duration (shorter at close range, longer at far range) → adaptive radar pulse duration (shorter for close targets, longer for far targets to maintain resolution)
- Bat's Doppler-shift compensation → radar Doppler processing that compensates for target motion
- Bat's jamming avoidance response → radar frequency-hopping or waveform diversity for interference mitigation

The key non-obvious insight is that bats dynamically adjust their FM sweep parameters based on the echo delay (target range), which is analogous to adaptive pulse compression in radar. This is NOT a surface analogy — it involves a specific signal-processing principle (time-bandwidth product optimization) that is present in both systems but described in completely different vocabulary.

### Validation path

The prediction can be validated against:
1. Established radar theory (time-bandwidth product, range resolution, clutter rejection)
2. Published bio-inspired radar literature (which the prior-art search will check)
3. Radar simulation (if the prediction specifies waveform parameters)

---

## 2. Frozen Input Package

### Document A: Source mechanism (bat echolocation)

A 1100-word technical description covering:
- FM sweep structure (downward frequency sweep, bandwidth, duration)
- Adaptive call duration (shorter at close range, longer at far range)
- Doppler-shift compensation (DSC) in horseshoe bats
- Jamming avoidance response (JAR)
- Echo processing and target classification
- Known failure modes (interference, clutter, range ambiguity)

Does NOT reference radar, signal processing, or waveform design.

### Document B: Target problem (maritime radar clutter)

A 800-word description covering:
- Maritime surveillance radar with clutter from sea waves
- Fixed waveform limitations (fixed pulse duration, fixed bandwidth)
- Clutter false alarm problem (sea clutter mimics small targets)
- Constraints (real-time processing, limited computational resources)
- What is needed (adaptive waveform that reduces clutter false alarms)

Does NOT reference bats, echolocation, or biology.

### SHA-256 manifest

Both documents hashed and recorded before execution.

---

## 3. Information Boundary

### What is in the input
- Bat echolocation mechanism (bioacoustics)
- Maritime radar clutter problem (signal processing)
- Physical constraints on both systems

### What is deliberately withheld
- Any reference connecting echolocation to radar
- The expected transfer (adaptive waveform design)
- Any mention of "bio-inspired radar" or "biomimetic signal processing"
- The evaluation criteria
- Prior literature on bat-inspired radar

### What constitutes "recoverable from input"
- Direct restatement of bat echolocation with "radar" substituted for "bat"
- Simple entity overlap ("both involve signals" or "both detect targets")
- Paraphrase of the source mechanism without mechanistic depth

### What constitutes the expected discovery
- A transfer that identifies a SPECIFIC signal-processing principle from echolocation (e.g., adaptive time-bandwidth product, Doppler compensation, frequency diversity for jamming avoidance) that maps to a SPECIFIC radar waveform parameter
- A quantitative prediction about clutter rejection improvement
- The prediction is physically testable against radar theory

---

## 4. Controls (all run under identical information boundaries)

### C1: Engine (full pipeline)
- Mechanism extraction → abstraction → transfer → hypotheses → adversarial
- Uses the frozen substrate and checkpointed loop

### C2: Generic LLM (same model, no pipeline)
- Prompt: "Read Document A and Document B. How might the mechanism in Document A apply to the problem in Document B? Produce a specific, falsifiable proposal."
- Same ZAI model, same temperature, same timeout

### C3: Retrieval-only
- TF-IDF entity overlap between the two documents
- Report shared entities and any connections

### C4: Human control (experimenter)
- Read both documents
- Produce a specific proposal
- Same time budget as the engine (~10 minutes of "thinking")

### C5: Matched null
- Document B only (radar problem, no bat mechanism)
- "Generate a solution for this radar problem"
- Tests whether the source mechanism adds value

---

## 5. Discovery Test

### Success conditions (ALL must be met)
1. Candidate transfer produced (not rejected at transfer stage)
2. At least one hypothesis classified as NON_TRIVIAL_TRANSFER or STRUCTURAL_INFERENCE
3. At least one hypothesis survives adversarial (ADVERSARIAL_SURVIVES or INCONCLUSIVE)
4. A falsifiable prediction is produced
5. The prediction is physically plausible (does not violate signal processing principles)

### Failure conditions (ANY one)
1. No transfer produced
2. All hypotheses classified as rediscovery (PARAPHRASED_IN_INPUT or DIRECT_COMPOSITION)
3. All hypotheses fail adversarial
4. No falsifiable prediction
5. Prediction is physically implausible
6. Engine output indistinguishable from retrieval baseline

---

## 6. Generator-vs-Filter Diagnostic

Same as DXP-002, plus the capability ceiling comparison:

| Outcome | Engine | Generic LLM | Retrieval | Human | Null | Diagnosis |
|---|---|---|---|---|---|---|
| Case 1 | FAIL | FAIL | FAIL | FAIL | FAIL | Challenge problem (too hard for anyone) |
| Case 2 | FAIL | PASS | FAIL | PASS | FAIL | Generator/architecture deficit |
| Case 3 | FAIL | FAIL | FAIL | PASS | FAIL | LLM limitation (human can, LLM can't) |
| Case 4 | PASS+survives | ? | ? | ? | FAIL | Approaching North Star — proceed to prior-art + experiment |
| Case 5 | candidates killed | ? | ? | ? | FAIL | Filter problem (over-aggressive adversarial) |

---

## 7. Pre-registration

Frozen before execution:
- Challenge (bat echolocation → maritime radar clutter)
- Input documents
- Expected transfer (adaptive waveform design)
- Evaluation criteria
- Controls
- Capability ceiling matrix
- Failure classification scheme

Cannot be changed after execution.

---

## 8. Stop Conditions

Same as DXP-001/002, plus:
6. Never optimize the engine to pass a discovery case it has already seen.
7. Do not modify the generator, adversarial gate, or scorer based on DXP-001/002 outcomes.
8. If the human control also fails, the challenge is too hard — record and stop.

---

## 9. Binary Outcome

### DISCOVERY (ALL must be met)
1. Non-trivial transfer (not recoverable from input)
2. Survives adversarial analysis
3. Produces a falsifiable prediction
4. Prediction is physically plausible
5. Prediction is not produced by retrieval-only baseline

### NOT DISCOVERY (ANY one)
1. No transfer produced
2. Transfer is recoverable from input
3. All candidates fail adversarial
4. No falsifiable prediction
5. Prediction is physically implausible
6. Output indistinguishable from retrieval baseline

### Capability ceiling classification (regardless of DISCOVERY/NOT DISCOVERY)
The outcome is classified into one of:
- **CHALLENGE_PROBLEM** (everyone fails — the transfer doesn't exist or is too hard)
- **GENERATOR_DEFICIT** (engine fails, controls succeed — the engine's pipeline is the bottleneck)
- **FILTER_PROBLEM** (engine generates candidates, filter kills them all — over-aggressive adversarial)
- **LLM_LIMITATION** (engine and generic LLM fail, human succeeds — the model can't reason about this)
- **APPROACHING_NORTH_STAR** (engine succeeds where controls fail — proceed to prior-art + experiment)
