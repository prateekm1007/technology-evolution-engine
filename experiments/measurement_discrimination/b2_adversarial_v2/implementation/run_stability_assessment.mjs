#!/usr/bin/env node
/**
 * run_stability_assessment.mjs — n=5 stability runner (REPORTING ONLY)
 *
 * Per CTO directive (round-82):
 *   - Calls the EXISTING FROZEN detector (no modifications to detector,
 *     prompt, or code that affects semantic behavior)
 *   - 5 independent executions per public case (65 LLM calls total)
 *   - No prompt changes, no code changes, no threshold changes,
 *     no case-specific corrections
 *   - Emits machine facts only
 *
 * Output:
 *   - Per-case: run_1..run_5 labels, majority label, unanimity/agreement,
 *     trace validity
 *   - Summary: schema validity, stability metrics, calibration accuracy,
 *     semantic failures, no-tuning confirmation
 */
import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { detect, FROZEN_CONFIG } from './b2_detector.mjs';
import { validateTrace } from './b2_trace_validator.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const FIXTURE_PATH = join(__dirname, '..', 'test_fixture.json');
const OUTPUT_DIR = join(__dirname, 'stability_results');

const N_RUNS = 5;

async function main() {
  console.log('B-2 Stability Assessment (n=5)');
  console.log('==============================');
  console.log(`Model: ${FROZEN_CONFIG.model_identifier}`);
  console.log(`Runs per case: ${N_RUNS}`);
  console.log(`Total LLM calls: ${N_RUNS * 13}`);
  console.log(`Detector: FROZEN (no modifications)`);
  console.log();

  const fixture = JSON.parse(readFileSync(FIXTURE_PATH, 'utf-8'));
  const source_a = fixture.source_a;
  const source_b = fixture.source_b;

  mkdirSync(OUTPUT_DIR, { recursive: true });

  const perCaseResults = [];

  for (const testCase of fixture.cases) {
    const params = {
      id: testCase.id,
      candidate: testCase.candidate,
      source_a,
      source_b,
    };

    console.log(`[${testCase.id}] ${testCase.candidate}`);
    console.log(`  expected: ${testCase.expected_label}`);

    const result = await detect(params, N_RUNS);

    // Extract per-run labels
    const runLabels = result.all_traces.map((t, i) => t.classification?.label || 'UNKNOWN');
    const runStates = result.all_traces.map(t => t.classification?.iss_state || 'UNKNOWN');

    // Majority label
    const majorityLabel = result.canonical_trace.classification?.label || 'UNKNOWN';
    const majorityState = result.canonical_trace.classification?.iss_state || 'UNKNOWN';

    // Agreement: count of runs matching majority
    const agreementCount = runLabels.filter(l => l === majorityLabel).length;
    const unanimous = agreementCount === N_RUNS;

    // Validate canonical trace
    const validation = validateTrace(result.canonical_trace);

    // Validate all traces
    const allValid = result.all_traces.every(t => validateTrace(t).valid);

    console.log(`  runs: ${runLabels.join(' | ')}`);
    console.log(`  majority: ${majorityLabel} (${majorityState})`);
    console.log(`  agreement: ${agreementCount}/${N_RUNS}${unanimous ? ' (UNANIMOUS)' : ''}`);
    console.log(`  tie: ${result.is_tie}`);
    console.log(`  canonical valid: ${validation.valid}`);
    console.log(`  all traces valid: ${allValid}`);
    if (!validation.valid) {
      console.log(`  validation errors: ${validation.errors.length}`);
      for (const e of validation.errors.slice(0, 3)) console.log(`    - ${e}`);
    }

    const match = majorityLabel === testCase.expected_label;
    // Also check against amended-spec expected (ADV-09)
    const amendedExpected = testCase.id === 'ADV-09' ? 'NOT_ADJUDICATED_BY_B2' : testCase.expected_label;
    const amendedMatch = majorityLabel === amendedExpected;

    console.log(`  match (fixture): ${match ? 'YES' : 'NO'}`);
    if (testCase.id === 'ADV-09') {
      console.log(`  match (amended spec): ${amendedMatch ? 'YES' : 'NO'}`);
    }
    console.log();

    perCaseResults.push({
      id: testCase.id,
      category: testCase.category,
      candidate: testCase.candidate,
      expected_label_fixture: testCase.expected_label,
      expected_label_amended: amendedExpected,
      run_labels: runLabels,
      run_states: runStates,
      majority_label: majorityLabel,
      majority_state: majorityState,
      agreement: `${agreementCount}/${N_RUNS}`,
      agreement_count: agreementCount,
      unanimous,
      is_tie: result.is_tie,
      canonical_trace_valid: validation.valid,
      all_traces_valid: allValid,
      match_fixture: match,
      match_amended: amendedMatch,
      label_distribution: result.label_distribution,
      canonical_trace: result.canonical_trace,
      all_traces: result.all_traces,
    });

    // Save per-run traces
    for (let i = 0; i < result.all_traces.length; i++) {
      writeFileSync(
        join(OUTPUT_DIR, `${testCase.id}.run${i + 1}.trace.json`),
        JSON.stringify(result.all_traces[i], null, 2)
      );
    }
  }

  // ===== SUMMARY =====
  const total = perCaseResults.length;

  // SCHEMA VALIDITY
  const allCanonicalValid = perCaseResults.every(r => r.canonical_trace_valid);
  const allAllValid = perCaseResults.every(r => r.all_traces_valid);
  const totalTraces = perCaseResults.length * N_RUNS;
  const validTraces = perCaseResults.reduce((sum, r) =>
    sum + r.all_traces.filter((_, i) => validateTrace(perCaseResults.find(p => p.id === r.id).all_traces[i]).valid).length, 0);

  // Recompute valid trace count properly
  let validTraceCount = 0;
  for (const r of perCaseResults) {
    for (const t of r.all_traces) {
      if (validateTrace(t).valid) validTraceCount++;
    }
  }

  // STABILITY
  const unanimousCount = perCaseResults.filter(r => r.unanimous).length;
  const fourOfFive = perCaseResults.filter(r => r.agreement_count === 4).length;
  const threeOfFive = perCaseResults.filter(r => r.agreement_count === 3).length;
  const unstable = perCaseResults.filter(r => r.agreement_count < 3 || r.is_tie).length;
  const meanAgreement = perCaseResults.reduce((s, r) => s + r.agreement_count, 0) / total;

  // CALIBRATION ACCURACY
  const fixtureMatches = perCaseResults.filter(r => r.match_fixture).length;
  const amendedMatches = perCaseResults.filter(r => r.match_amended).length;

  // SEMANTIC FAILURES (per amended spec)
  const semanticFailures = perCaseResults.filter(r => !r.match_amended).map(r => ({
    id: r.id,
    candidate: r.candidate,
    expected: r.expected_label_amended,
    got: r.majority_label,
    agreement: r.agreement,
  }));

  console.log('==============================');
  console.log('STABILITY ASSESSMENT SUMMARY');
  console.log('==============================');
  console.log();
  console.log('SCHEMA VALIDITY');
  console.log(`  Canonical traces valid: ${perCaseResults.filter(r => r.canonical_trace_valid).length}/${total}`);
  console.log(`  All ${N_RUNS} runs valid: ${perCaseResults.filter(r => r.all_traces_valid).length}/${total}`);
  console.log(`  Total valid traces: ${validTraceCount}/${totalTraces}`);
  console.log();
  console.log('STABILITY');
  console.log(`  Mean per-case agreement: ${meanAgreement.toFixed(2)}/${N_RUNS}`);
  console.log(`  Unanimous (5/5): ${unanimousCount}/${total}`);
  console.log(`  4/5 agreement: ${fourOfFive}/${total}`);
  console.log(`  3/5 agreement: ${threeOfFive}/${total}`);
  console.log(`  Unstable (<3/5 or tie): ${unstable}/${total}`);
  console.log();
  console.log('CALIBRATION ACCURACY (majority vote)');
  console.log(`  vs fixture labels: ${fixtureMatches}/${total}`);
  console.log(`  vs amended spec labels: ${amendedMatches}/${total}`);
  console.log();
  console.log('SEMANTIC FAILURES (per amended spec)');
  console.log(`  ${semanticFailures.length} cases wrong:`);
  for (const f of semanticFailures) {
    console.log(`    ${f.id}: '${f.candidate}' expected=${f.expected} got=${f.got} (${f.agreement})`);
  }
  console.log();
  console.log('NO-TUNING CONFIRMATION');
  console.log(`  Detector modified: NO`);
  console.log(`  Prompt modified: NO`);
  console.log(`  Code modified: NO`);
  console.log(`  Threshold changed: NO`);
  console.log(`  Case-specific corrections: NO`);
  console.log();

  // Save full report
  const report = {
    assessment: 'n=5 stability',
    model: FROZEN_CONFIG.model_identifier,
    n_runs: N_RUNS,
    total_llm_calls: N_RUNS * total,
    detector_modified: false,
    prompt_modified: false,
    code_modified: false,
    threshold_changed: false,
    case_specific_corrections: false,
    schema_validity: {
      canonical_traces_valid: perCaseResults.filter(r => r.canonical_trace_valid).length,
      all_runs_valid: perCaseResults.filter(r => r.all_traces_valid).length,
      total_traces: totalTraces,
      valid_traces: validTraceCount,
      total_cases: total,
    },
    stability: {
      mean_agreement: parseFloat(meanAgreement.toFixed(2)),
      unanimous: unanimousCount,
      four_of_five: fourOfFive,
      three_of_five: threeOfFive,
      unstable: unstable,
      total: total,
    },
    calibration_accuracy: {
      fixture_labels: fixtureMatches,
      amended_spec_labels: amendedMatches,
      total: total,
    },
    semantic_failures: semanticFailures,
    per_case: perCaseResults.map(r => ({
      id: r.id,
      category: r.category,
      candidate: r.candidate,
      run_labels: r.run_labels,
      majority_label: r.majority_label,
      majority_state: r.majority_state,
      agreement: r.agreement,
      unanimous: r.unanimous,
      is_tie: r.is_tie,
      canonical_trace_valid: r.canonical_trace_valid,
      all_traces_valid: r.all_traces_valid,
      match_fixture: r.match_fixture,
      match_amended: r.match_amended,
    })),
  };

  writeFileSync(
    join(OUTPUT_DIR, 'stability_report.json'),
    JSON.stringify(report, null, 2)
  );

  console.log(`Full report: ${OUTPUT_DIR}/stability_report.json`);
  console.log(`Per-run traces: ${OUTPUT_DIR}/*.runN.trace.json`);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
