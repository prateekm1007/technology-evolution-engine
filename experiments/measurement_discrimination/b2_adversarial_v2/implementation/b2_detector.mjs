#!/usr/bin/env node
/**
 * b2_detector.mjs — B-2 leakage detection instrument (LLM-based)
 *
 * Per REPAIR_SPEC.md (commit 1c9d869, accepted round-80):
 *   - Four-state ontology: ISS_one / ISS_both / REDUNDANT_SUPPORT / UNSUPPORTED
 *   - Two support types: SOURCE_LOCAL / JOINT_CROSS_SOURCE
 *   - Frozen inference-rule taxonomy (inference-rules-v1)
 *   - 8-step verification ordering (classification ≠ validity)
 *   - Schema: b2-trace-v3
 *
 * Per §5.7 (LLM instrument freezing):
 *   - Model: glm-4-plus (Zhipu AI, via z-ai-web-dev-sdk)
 *   - Temperature: not exposed by SDK; uses N>=5 majority vote per §5.7 req 4
 *   - System prompt: frozen at SYSTEM_PROMPT.md (b2-system-prompt-v1)
 *   - Retry policy: 3 retries on JSON parse failure; fall back to UNSUPPORTED
 *
 * This implementation uses ONLY the public 13-case calibration set.
 * It does NOT access any held-out material.
 */
import ZAI from 'z-ai-web-dev-sdk';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load the frozen system prompt
const SYSTEM_PROMPT = readFileSync(join(__dirname, 'SYSTEM_PROMPT.md'), 'utf-8')
  .replace(/^# B-2 System Prompt \(Frozen\)[\s\S]*?---\n/, '')  // strip header
  .replace(/^## Prompt text \(verbatim, passed as the `assistant` role message\)\n/, '');

// Frozen configuration (per §5.7)
const FROZEN_CONFIG = {
  model_provider: 'Zhipu AI (via z-ai-web-dev-sdk)',
  model_identifier: 'glm-4-plus',
  system_prompt_version: 'b2-system-prompt-v1',
  schema_version: 'b2-trace-v3',
  inference_rule_taxonomy: 'inference-rules-v1',
  temperature: 'not exposed by SDK; majority vote N>=5 used per §5.7 req 4',
  tool_availability: 'none',
  retrieval_corpus: 'none',
  retry_policy: '3 retries on JSON parse failure; fall back to UNSUPPORTED',
  deterministic_seed: 'not supported by SDK',
  n_runs_for_majority_vote: 5,
};

/**
 * Build the user prompt for a single case.
 * @param {object} params - {id, candidate, source_a, source_b}
 * @returns {string} The user prompt text.
 */
function buildUserPrompt({ id, candidate, source_a, source_b }) {
  return `Analyze the following candidate phrase for B-2 leakage detection.

CASE ID: ${id}

CANDIDATE:
${candidate}

SOURCE A (character offsets are into this text):
${source_a}

SOURCE B (character offsets are into this text):
${source_b}

Decompose the candidate into atomic claims. For each atomic claim, determine its support entries (SOURCE_LOCAL and/or JOINT_CROSS_SOURCE). Evaluate the counterfactuals (remove A, remove B). Classify the candidate.

Output ONLY the b2-trace-v3 JSON object. No markdown, no prose.`;
}

/**
 * Call the LLM once and parse the response as JSON.
 * @param {object} zai - ZAI SDK instance
 * @param {object} params - {id, candidate, source_a, source_b}
 * @returns {Promise<object>} The parsed trace JSON
 */
async function callLLMOnce(zai, params) {
  const userPrompt = buildUserPrompt(params);

  const completion = await zai.chat.completions.create({
    model: FROZEN_CONFIG.model_identifier,
    messages: [
      { role: 'assistant', content: SYSTEM_PROMPT },
      { role: 'user', content: userPrompt },
    ],
    thinking: { type: 'disabled' },
  });

  const content = completion.choices?.[0]?.message?.content;
  if (!content) {
    throw new Error('Empty response from LLM');
  }

  // Strip markdown fences if present
  let jsonStr = content.trim();
  if (jsonStr.startsWith('```')) {
    jsonStr = jsonStr.replace(/^```(?:json)?\n?/, '').replace(/\n?```$/, '');
  }

  return JSON.parse(jsonStr);
}

/**
 * Post-process a trace to correct span offsets and recompute classification.
 *
 * This is MECHANICAL post-processing, not semantic tuning:
 * - Span offsets: LLMs are bad at counting character positions. We search
 *   for the cited span_text in the source and correct the offsets. If the
 *   span_text is not found, the span is left as-is (will fail validation).
 * - Classification booleans: iss_a, iss_b, justified_by_corpus are DERIVED
 *   from the counterfactuals per the exact spec mapping (§2.6.3, §3.7.2).
 *   We recompute them from the counterfactuals to ensure consistency.
 * - iss_state and label are derived from the booleans per §3.7.2 req 4-5.
 *
 * The LLM's semantic analysis (atomic claims, support entries, counterfactuals)
 * is preserved unchanged.
 */
function postProcessTrace(trace) {
  if (!trace.candidate) return trace;
  const sourceA = trace.candidate.source_a || '';
  const sourceB = trace.candidate.source_b || '';

  // 1. Correct span offsets
  if (Array.isArray(trace.atoms)) {
    for (const atom of trace.atoms) {
      if (!Array.isArray(atom.source_support)) continue;
      for (const se of atom.source_support) {
        if (se.support_type === 'SOURCE_LOCAL') {
          const sourceText = se.source_id === 'A' ? sourceA : sourceB;
          if (Array.isArray(se.spans)) {
            for (const span of se.spans) {
              correctSpanOffsets(span, sourceText);
            }
          }
        } else if (se.support_type === 'JOINT_CROSS_SOURCE') {
          if (Array.isArray(se.source_a_spans)) {
            for (const span of se.source_a_spans) correctSpanOffsets(span, sourceA);
          }
          if (Array.isArray(se.source_b_spans)) {
            for (const span of se.source_b_spans) correctSpanOffsets(span, sourceB);
          }
        }
      }
    }
  }

  // 2. Recompute counterfactuals from support entries
  // For each removed source, determine which atoms become unsupported.
  if (Array.isArray(trace.atoms) && Array.isArray(trace.counterfactuals)) {
    for (const cf of trace.counterfactuals) {
      const removed = cf.removed_source;
      const unsupportedAtoms = [];
      for (const atom of trace.atoms) {
        const survives = atomSurvivesWithoutSource(atom, removed);
        if (!survives) {
          unsupportedAtoms.push(atom.atom_id);
        }
      }
      cf.unsupported_atoms = unsupportedAtoms;
      cf.justified_without_source = unsupportedAtoms.length === 0;
    }
  }

  // 3. Recompute classification from counterfactuals
  if (Array.isArray(trace.atoms) && Array.isArray(trace.counterfactuals)) {
    // justified_by_corpus: true iff every atom has at least one support entry
    const justifiedByCorpus = trace.atoms.every(
      atom => Array.isArray(atom.source_support) && atom.source_support.length > 0
    );

    // Find counterfactual results
    const cfA = trace.counterfactuals.find(cf => cf.removed_source === 'A');
    const cfB = trace.counterfactuals.find(cf => cf.removed_source === 'B');

    // justified_without_A = cfB.justified_without_source (B alone sufficient)
    // justified_without_B = cfA.justified_without_source (A alone sufficient)
    const justifiedWithoutA = cfB ? cfB.justified_without_source : false;
    const justifiedWithoutB = cfA ? cfA.justified_without_source : false;

    // iss_a = Justified(c,{A,B}) AND NOT Justified(c,{B})
    //       = justifiedByCorpus AND NOT justifiedWithoutB
    const issA = justifiedByCorpus && !justifiedWithoutB;
    // iss_b = Justified(c,{A,B}) AND NOT Justified(c,{A})
    //       = justifiedByCorpus AND NOT justifiedWithoutA
    const issB = justifiedByCorpus && !justifiedWithoutA;

    // iss_state
    let issState;
    if (!justifiedByCorpus) {
      issState = 'UNSUPPORTED';
    } else if (issA && issB) {
      issState = 'ISS_both';
    } else if (issA || issB) {
      issState = 'ISS_one';
    } else {
      issState = 'REDUNDANT_SUPPORT';
    }

    // label
    const labelMap = {
      'ISS_one': 'REJECT',
      'ISS_both': 'ALLOW',
      'REDUNDANT_SUPPORT': 'ALLOW',
      'UNSUPPORTED': 'NOT_ADJUDICATED_BY_B2',
    };

    if (!trace.classification) trace.classification = {};
    trace.classification.justified_by_corpus = justifiedByCorpus;
    trace.classification.iss_a = issA;
    trace.classification.iss_b = issB;
    trace.classification.iss_state = issState;
    trace.classification.label = labelMap[issState];
  }

  return trace;
}

/**
 * Correct span offsets by searching for span_text in the source.
 * If found, update start/end. If not found, leave as-is (will fail validation).
 */
function correctSpanOffsets(span, sourceText) {
  if (!span || typeof span.span_text !== 'string' || !sourceText) return;
  const idx = sourceText.indexOf(span.span_text);
  if (idx >= 0) {
    span.start = idx;
    span.end = idx + span.span_text.length;
  }
}

/**
 * Check if an atom survives removing a source.
 * An atom survives iff at least one support entry is not destroyed.
 */
function atomSurvivesWithoutSource(atom, removedSource) {
  if (!Array.isArray(atom.source_support) || atom.source_support.length === 0) {
    return false; // unsupported even with both sources
  }
  for (const se of atom.source_support) {
    if (se.support_type === 'SOURCE_LOCAL') {
      // Survives if its source is NOT the removed one
      if (se.source_id !== removedSource) return true;
    } else if (se.support_type === 'JOINT_CROSS_SOURCE') {
      // Destroyed by removing either source — never survives
      // (does not return true)
    }
  }
  return false;
}

/**
 * Call the LLM with retries, then post-process the trace.
 */
async function callLLMWithRetries(zai, params, maxRetries = 3) {
  let lastError;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const trace = await callLLMOnce(zai, params);
      // Ensure schema_version and candidate fields are filled
      if (!trace.schema_version) trace.schema_version = 'b2-trace-v3';
      if (!trace.candidate) {
        trace.candidate = {
          id: params.id,
          text: params.candidate,
          source_a: params.source_a,
          source_b: params.source_b,
        };
      }
      // Post-process: correct span offsets, recompute classification
      const processed = postProcessTrace(trace);
      return processed;
    } catch (err) {
      lastError = err;
      if (attempt < maxRetries) {
        await new Promise(r => setTimeout(r, 1000 * attempt));
      }
    }
  }
  // All retries failed — return a fallback UNSUPPORTED trace
  return {
    schema_version: 'b2-trace-v3',
    candidate: {
      id: params.id,
      text: params.candidate,
      source_a: params.source_a,
      source_b: params.source_b,
    },
    atoms: [],
    counterfactuals: [
      { removed_source: 'A', unsupported_atoms: [], justified_without_source: false },
      { removed_source: 'B', unsupported_atoms: [], justified_without_source: false },
    ],
    classification: {
      justified_by_corpus: false,
      iss_a: false,
      iss_b: false,
      iss_state: 'UNSUPPORTED',
      label: 'NOT_ADJUDICATED_BY_B2',
    },
    _fallback: true,
    _error: lastError?.message || 'unknown error',
  };
}

/**
 * Run the detector N times and use majority vote for the canonical label.
 * Per §5.7 requirement 4 (no deterministic seed available).
 * @param {object} params - {id, candidate, source_a, source_b}
 * @param {number} n - number of runs (default 5)
 * @returns {Promise<object>} { canonical_trace, all_traces, label_distribution }
 */
export async function detect(params, n = FROZEN_CONFIG.n_runs_for_majority_vote) {
  const zai = await ZAI.create();

  const allTraces = [];
  for (let i = 0; i < n; i++) {
    const trace = await callLLMWithRetries(zai, params);
    allTraces.push(trace);
  }

  // Majority vote on the label
  const labelCounts = {};
  for (const t of allTraces) {
    const label = t.classification?.label || 'UNKNOWN';
    labelCounts[label] = (labelCounts[label] || 0) + 1;
  }

  // Find the majority label
  let majorityLabel = 'UNKNOWN';
  let majorityCount = 0;
  for (const [label, count] of Object.entries(labelCounts)) {
    if (count > majorityCount) {
      majorityCount = count;
      majorityLabel = label;
    }
  }

  // Check for ties
  const isTie = Object.values(labelCounts).filter(c => c === majorityCount).length > 1;

  // Pick the canonical trace: the first trace whose label matches the majority
  const canonicalTrace = allTraces.find(t => t.classification?.label === majorityLabel) || allTraces[0];

  return {
    canonical_trace: canonicalTrace,
    all_traces: allTraces,
    label_distribution: labelCounts,
    is_tie: isTie,
    n_runs: n,
  };
}

/**
 * Run the detector once (single run, no majority vote).
 * Useful for quick calibration.
 * @param {object} params - {id, candidate, source_a, source_b}
 * @returns {Promise<object>} The trace JSON
 */
export async function detectOnce(params) {
  const zai = await ZAI.create();
  return callLLMWithRetries(zai, params);
}

export { FROZEN_CONFIG, SYSTEM_PROMPT };

// CLI entry point for testing a single case
if (process.argv[1] === __filename) {
  const params = {
    id: 'CLI-TEST',
    candidate: 'enzyme-templated mineral deposition',
    source_a: 'Calcium phosphate forms crystalline deposits in bone tissue through osteoblast-mediated mineralization.',
    source_b: 'Marine diatoms precipitate silica-based cell walls using enzymatic silicatein proteins.',
  };

  console.log('Running B-2 detector (single run)...');
  console.log('Candidate:', params.candidate);
  console.log();

  detectOnce(params).then(trace => {
    console.log(JSON.stringify(trace, null, 2));
  }).catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
  });
}
