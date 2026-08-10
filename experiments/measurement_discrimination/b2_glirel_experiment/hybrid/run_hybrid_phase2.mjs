#!/usr/bin/env node
/**
 * run_hybrid_phase2.mjs — Phase 2: GLM hybrid adjudication using GLiREL evidence.
 *
 * Loads evidence_graphs.json from Phase 1 (Kaggle), constructs a hybrid prompt
 * that includes GLiREL's structured evidence, calls the frozen GLM detector
 * for each case, and compares baseline (GLM-only) vs hybrid (GLiREL+GLM).
 *
 * Does NOT modify the frozen B-2 detector. The hybrid prompt is SEPARATE from
 * the frozen SYSTEM_PROMPT.md. The frozen detector is called as-is for baseline.
 *
 * Per CTO directive: GLiREL output is evidence extraction, not truth.
 * The LLM must independently determine whether extracted evidence supports the candidate.
 */
import ZAI from 'z-ai-web-dev-sdk';
import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ── Configuration ──
const EVIDENCE_PATH = process.argv[2] || join(__dirname, 'results', 'glirel', 'evidence_graphs.json');
const OUTPUT_DIR = join(__dirname, 'results', 'hybrid');
const N_RUNS = 1; // Single run for speed; frozen detector used N=5 for stability

// ── Model selection ──
const REQUESTED_MODEL = 'glm-5.2';
let actualModel = 'glm-4-plus'; // Default fallback
let fallbackUsed = true;
let fallbackReason = 'API accepts any model name without validation; response model field always returns glm-4-plus; cannot confirm GLM-5.2 is actually available';

mkdirSync(OUTPUT_DIR, { recursive: true });

// ── Hybrid system prompt (SEPARATE from frozen SYSTEM_PROMPT.md) ──
const HYBRID_PROMPT = `You are a B-2 leakage detection instrument with structured evidence assistance.

You receive:
1. A candidate phrase
2. Source A and Source B texts
3. Structured evidence extracted by GLiREL (a relation extraction model)

CRITICAL: GLiREL output is EVIDENCE EXTRACTION, NOT TRUTH. GLiREL extracts
relations between entities, but:
- GLiREL extracting a relation does NOT mean the relation is scientifically valid
- GLiREL may extract false relations
- GLiREL may miss important relations
- You must INDEPENDENTLY determine whether the evidence supports the candidate

Your job is the same as the standard B-2 detector: determine whether the candidate
is leaked from one source (ISS_one → REJECT), genuinely cross-source (ISS_both → ALLOW),
redundantly supported (REDUNDANT_SUPPORT → ALLOW), or unsupported (UNSUPPORTED → NOT_ADJUDICATED_BY_B2).

Use the GLiREL evidence as a STARTING POINT for your analysis, but do not trust it blindly.
Verify each relation against the source text yourself.

## ONTOLOGY (same as frozen B-2)
- ISS_one: candidate justified by corpus, one source alone sufficient → REJECT
- ISS_both: candidate justified by corpus, neither source alone sufficient → ALLOW
- REDUNDANT_SUPPORT: both sources independently justify → ALLOW
- UNSUPPORTED: candidate NOT justified by corpus → NOT_ADJUDICATED_BY_B2

## OUTPUT
Output ONLY a valid JSON object with this schema:
{
  "schema_version": "b2-trace-v3",
  "candidate": {"id": "...", "text": "...", "source_a": "...", "source_b": "..."},
  "atoms": [...],
  "counterfactuals": [...],
  "classification": {
    "justified_by_corpus": <boolean>,
    "iss_a": <boolean>,
    "iss_b": <boolean>,
    "iss_state": "<ISS_one|ISS_both|REDUNDANT_SUPPORT|UNSUPPORTED>",
    "label": "<REJECT|ALLOW|NOT_ADJUDICATED_BY_B2>"
  },
  "evidence_assessment": {
    "glirel_relations_used": <int>,
    "glirel_relations_rejected": <int>,
    "glirel_evidence_helpful": <boolean>,
    "notes": "<brief explanation>"
  }
}

Output ONLY the JSON. No markdown, no prose.`;

function buildHybridUserPrompt(caseData, evidence) {
  const { id, candidate, source_a_text: sourceA, source_b_text: sourceB } = caseData;

  // Format GLiREL evidence
  const edgesA = (evidence.edges_a || []).slice(0, 10).map((e, i) =>
    `  ${i+1}. ${e.label}(${e.head_text}, ${e.tail_text}) score=${(e.score || 0).toFixed(3)} spans=${e.spans_valid ? 'valid' : 'invalid'}`
  ).join('\n');
  const edgesB = (evidence.edges_b || []).slice(0, 10).map((e, i) =>
    `  ${i+1}. ${e.label}(${e.head_text}, ${e.tail_text}) score=${(e.score || 0).toFixed(3)} spans=${e.spans_valid ? 'valid' : 'invalid'}`
  ).join('\n');

  return `Analyze the following candidate for B-2 leakage detection.

CASE ID: ${id}

CANDIDATE:
${candidate}

SOURCE A:
${sourceA}

SOURCE B:
${sourceB}

GLiREL EXTRACTED EVIDENCE (Source A relations — top 10):
${edgesA || '  (none extracted)'}

GLiREL EXTRACTED EVIDENCE (Source B relations — top 10):
${edgesB || '  (none extracted)'}

IMPORTANT: The GLiREL evidence above is extracted by a relation model. It may contain
errors. Verify each relation against the source text yourself. Do not assume a relation
is true just because GLiREL extracted it.

Analyze the candidate and output the b2-trace-v3 JSON.`;
}

async function main() {
  console.log('B-2 GLiREL Hybrid Experiment — Phase 2: GLM Adjudication');
  console.log('==========================================================');
  console.log(`Requested model: ${REQUESTED_MODEL}`);
  console.log(`Actual model: ${actualModel} (fallback: ${fallbackUsed})`);
  console.log(`Evidence: ${EVIDENCE_PATH}`);
  console.log();

  // Load evidence graphs
  const evidenceData = JSON.parse(readFileSync(EVIDENCE_PATH, 'utf-8'));
  console.log(`Loaded ${evidenceData.length} cases from evidence graphs`);

  // Load fixture for expected labels
  const fixturePath = join(__dirname, '..', '..', 'test_fixture.json');
  const fixture = JSON.parse(readFileSync(fixturePath, 'utf-8'));

  // Init ZAI SDK
  const zai = await ZAI.create();

  // Test model availability
  console.log('Testing model availability...');
  try {
    const testCompletion = await zai.chat.completions.create({
      model: REQUESTED_MODEL,
      messages: [
        { role: 'assistant', content: 'Reply with: OK' },
        { role: 'user', content: 'test' },
      ],
      thinking: { type: 'disabled' },
    });
    const responseModel = testCompletion.model || 'unknown';
    console.log(`  Requested: ${REQUESTED_MODEL}, Response model: ${responseModel}`);
    if (responseModel === REQUESTED_MODEL || responseModel === 'glm-5.2') {
      actualModel = REQUESTED_MODEL;
      fallbackUsed = false;
      fallbackReason = '';
      console.log('  GLM-5.2 confirmed available!');
    } else {
      console.log(`  GLM-5.2 NOT confirmed (response says ${responseModel}). Using ${actualModel}.`);
    }
  } catch (e) {
    console.log(`  GLM-5.2 request failed: ${e.message}. Using ${actualModel}.`);
  }

  const modelSelection = {
    requested_model: REQUESTED_MODEL,
    actual_model: actualModel,
    glm_5_2_available: !fallbackUsed,
    fallback_used: fallbackUsed,
    fallback_reason: fallbackReason,
  };
  writeFileSync(join(OUTPUT_DIR, '..', 'diagnostics', 'model_selection.json'),
    JSON.stringify(modelSelection, null, 2));
  console.log();

  // Run hybrid adjudication for each case
  const hybridResults = [];

  for (const evidence of evidenceData) {
    const tc = fixture.cases.find(c => c.id === evidence.case_id);
    if (!tc) continue;

    console.log(`[${evidence.case_id}] ${evidence.candidate}`);
    console.log(`  expected: ${tc.expected_label}`);

    const userPrompt = buildHybridUserPrompt(evidence, evidence);

    try {
      const completion = await zai.chat.completions.create({
        model: actualModel,
        messages: [
          { role: 'assistant', content: HYBRID_PROMPT },
          { role: 'user', content: userPrompt },
        ],
        thinking: { type: 'disabled' },
      });

      let content = completion.choices?.[0]?.message?.content || '';
      // Strip markdown fences
      content = content.trim().replace(/^```(?:json)?\n?/, '').replace(/\n?```$/, '');

      let trace;
      try {
        trace = JSON.parse(content);
      } catch (parseErr) {
        trace = { parse_error: parseErr.message, raw_content: content.substring(0, 500) };
      }

      const hybridLabel = trace.classification?.label || 'PARSE_ERROR';
      const hybridState = trace.classification?.iss_state || 'UNKNOWN';
      const match = hybridLabel === tc.expected_label;

      // Also check amended spec (ADV-09)
      const amendedExpected = evidence.case_id === 'ADV-09' ? 'NOT_ADJUDICATED_BY_B2' : tc.expected_label;
      const amendedMatch = hybridLabel === amendedExpected;

      console.log(`  hybrid: ${hybridLabel} (${hybridState}) ${amendedMatch ? '✓' : '✗'}`);

      // Evidence assessment
      const evAssessment = trace.evidence_assessment || {};
      if (evAssessment.glirel_evidence_helpful !== undefined) {
        console.log(`  evidence helpful: ${evAssessment.glirel_evidence_helpful}, used: ${evAssessment.glirel_relations_used || 0}, rejected: ${evAssessment.glirel_relations_rejected || 0}`);
      }

      hybridResults.push({
        case_id: evidence.case_id,
        candidate: evidence.candidate,
        expected_label: tc.expected_label,
        expected_amended: amendedExpected,
        hybrid_label: hybridLabel,
        hybrid_state: hybridState,
        match_amended: amendedMatch,
        glirel_evidence_stats: evidence.stats,
        evidence_assessment: evAssessment,
        trace,
      });

      // Save individual trace
      writeFileSync(join(OUTPUT_DIR, `${evidence.case_id}.trace.json`),
        JSON.stringify(trace, null, 2));
    } catch (err) {
      console.log(`  ERROR: ${err.message}`);
      hybridResults.push({
        case_id: evidence.case_id,
        candidate: evidence.candidate,
        expected_label: tc.expected_label,
        hybrid_label: 'ERROR',
        match_amended: false,
        error: err.message,
      });
    }
  }

  // ── Load baseline results for comparison ──
  const baselineDir = join(__dirname, '..', '..', 'implementation', 'stability_results');
  let baselineResults = [];
  try {
    const baselineSummary = JSON.parse(readFileSync(join(baselineDir, 'stability_report.json'), 'utf-8'));
    baselineResults = baselineSummary.per_case || [];
  } catch (e) {
    console.log('\nWARNING: Could not load baseline results for comparison');
  }

  // ── Build comparison ──
  const comparison = {
    model_selection: modelSelection,
    summary: {
      total_cases: hybridResults.length,
      hybrid_matches: hybridResults.filter(r => r.match_amended).length,
      hybrid_errors: hybridResults.filter(r => r.hybrid_label === 'ERROR' || r.hybrid_label === 'PARSE_ERROR').length,
    },
    per_case: hybridResults.map(r => {
      const baseline = baselineResults.find(b => b.id === r.case_id);
      return {
        case_id: r.case_id,
        candidate: r.candidate,
        expected: r.expected_amended,
        baseline_label: baseline?.majority_label || 'N/A',
        baseline_agreement: baseline?.agreement || 'N/A',
        hybrid_label: r.hybrid_label,
        hybrid_state: r.hybrid_state,
        baseline_match: baseline?.match || false,
        hybrid_match: r.match_amended,
        glirel_evidence_used: r.evidence_assessment?.glirel_relations_used || 0,
        glirel_evidence_helpful: r.evidence_assessment?.glirel_evidence_helpful || null,
      };
    }),
  };

  // Known failure cases
  const failureIds = ['ADV-05', 'ADV-06', 'ADV-07', 'ADV-08', 'ADV-13'];
  comparison.failure_cases = comparison.per_case.filter(c => failureIds.includes(c.case_id));

  // Save results
  writeFileSync(join(OUTPUT_DIR, 'hybrid_results.json'),
    JSON.stringify(hybridResults, null, 2));
  writeFileSync(join(OUTPUT_DIR, '..', 'comparison.json'),
    JSON.stringify(comparison, null, 2));

  // ── Print summary ──
  console.log('\n' + '='.repeat(60));
  console.log('HYBRID EXPERIMENT SUMMARY');
  console.log('='.repeat(60));
  console.log(`Model: ${actualModel} (fallback: ${fallbackUsed})`);
  console.log(`Total cases: ${comparison.summary.total_cases}`);
  console.log(`Hybrid matches: ${comparison.summary.hybrid_matches}/${comparison.summary.total_cases}`);
  console.log();

  console.log('PER-CASE COMPARISON:');
  console.log('-'.repeat(60));
  for (const c of comparison.per_case) {
    const bStatus = c.baseline_match ? '✓' : '✗';
    const hStatus = c.hybrid_match ? '✓' : '✗';
    console.log(`  ${c.case_id}: expected=${c.expected}`);
    console.log(`    baseline: ${c.baseline_label} ${bStatus} (${c.baseline_agreement})`);
    console.log(`    hybrid:   ${c.hybrid_label} ${hStatus}`);
    if (c.glirel_evidence_helpful !== null) {
      console.log(`    evidence: ${c.glirel_evidence_used} used, helpful=${c.glirel_evidence_helpful}`);
    }
  }

  console.log('\nFAILURE CASES (ADV-05,06,07,08,13):');
  console.log('-'.repeat(60));
  for (const c of comparison.failure_cases) {
    const improved = !c.baseline_match && c.hybrid_match;
    const regressed = c.baseline_match && !c.hybrid_match;
    const status = improved ? 'IMPROVED' : regressed ? 'REGRESSED' : 'UNCHANGED';
    console.log(`  ${c.case_id} ({c.candidate}): ${status}`);
    console.log(`    baseline: ${c.baseline_label} ${c.baseline_match ? '✓' : '✗'}");
    console.log(`    hybrid:   ${c.hybrid_label} ${c.hybrid_match ? '✓' : '✗'}`);
  }

  console.log(`\nResults saved to: ${OUTPUT_DIR}/`);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
