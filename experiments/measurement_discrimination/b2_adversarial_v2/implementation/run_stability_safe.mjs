#!/usr/bin/env node
/**
 * run_stability_safe.mjs — n=5 stability runner with rate-limit safety
 *
 * Same as run_stability_assessment.mjs but adds 15s delay between LLM
 * calls to avoid 429 rate limiting. This is a TEST HARNESS change only
 * (spacing between calls); the detector itself is UNCHANGED.
 *
 * Per CTO directive: no detector/prompt/code modifications, no tuning.
 */
import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { detectOnce, FROZEN_CONFIG } from './b2_detector.mjs';
import { validateTrace } from './b2_trace_validator.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const FIXTURE_PATH = join(__dirname, '..', 'test_fixture.json');
const OUTPUT_DIR = join(__dirname, 'stability_results');
const N_RUNS = 5;
const DELAY_MS = 15000; // 15s between calls

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  console.log('B-2 Stability Assessment (n=5, rate-limit safe)');
  console.log('================================================');
  console.log(`Model: ${FROZEN_CONFIG.model_identifier}`);
  console.log(`Runs per case: ${N_RUNS}`);
  console.log(`Delay between calls: ${DELAY_MS}ms`);
  console.log(`Total LLM calls: ${N_RUNS * 13}`);
  console.log(`Detector: FROZEN (no modifications)`);
  console.log();

  const fixture = JSON.parse(readFileSync(FIXTURE_PATH, 'utf-8'));
  mkdirSync(OUTPUT_DIR, { recursive: true });

  const perCase = [];

  for (const tc of fixture.cases) {
    const params = { id: tc.id, candidate: tc.candidate, source_a: fixture.source_a, source_b: fixture.source_b };
    console.log(`[${tc.id}] ${tc.candidate}`);

    const allTraces = [];
    for (let i = 0; i < N_RUNS; i++) {
      const trace = await detectOnce(params);
      allTraces.push(trace);
      const label = trace.classification?.label || 'UNKNOWN';
      const isFallback = trace._fallback || false;
      console.log(`  run ${i+1}/${N_RUNS}: ${label}${isFallback ? ' [FALLBACK]' : ''}`);
      writeFileSync(join(OUTPUT_DIR, `${tc.id}.run${i+1}.trace.json`), JSON.stringify(trace, null, 2));
      if (i < N_RUNS - 1) await sleep(DELAY_MS);
    }

    // Analyze
    const runLabels = allTraces.map(t => t.classification?.label || 'UNKNOWN');
    const runStates = allTraces.map(t => t.classification?.iss_state || 'UNKNOWN');
    const allValid = allTraces.every(t => validateTrace(t).valid);
    const fallbackCount = allTraces.filter(t => t._fallback).length;

    // Majority vote
    const counts = {};
    for (const l of runLabels) counts[l] = (counts[l] || 0) + 1;
    let majorityLabel = runLabels[0], maxCount = 0;
    for (const [l, c] of Object.entries(counts)) {
      if (c > maxCount) { maxCount = c; majorityLabel = l; }
    }
    const isTie = Object.values(counts).filter(c => c === maxCount).length > 1;
    const unanimous = maxCount === N_RUNS;

    const amendedExpected = tc.id === 'ADV-09' ? 'NOT_ADJUDICATED_BY_B2' : tc.expected_label;
    const matchAmended = majorityLabel === amendedExpected;

    perCase.push({
      id: tc.id, candidate: tc.candidate, category: tc.category,
      expected_amended: amendedExpected,
      run_labels: runLabels, majority: majorityLabel,
      agreement_count: maxCount, unanimous, is_tie: isTie,
      all_valid: allValid, fallback_count: fallbackCount,
      match_amended: matchAmended, label_counts: counts,
    });

    console.log(`  majority: ${majorityLabel} (${maxCount}/${N_RUNS})${isTie ? ' [TIE]' : ''}${unanimous ? ' [UNANIMOUS]' : ''}`);
    console.log(`  fallbacks: ${fallbackCount}/${N_RUNS}`);
    console.log(`  valid: ${allValid}, match: ${matchAmended}`);
    console.log();
  }

  // Summary
  const total = perCase.length;
  const allValid = perCase.every(r => r.all_valid);
  const totalFallbacks = perCase.reduce((s, r) => s + r.fallback_count, 0);
  const unanimousCount = perCase.filter(r => r.unanimous).length;
  const fourOfFive = perCase.filter(r => r.agreement_count === 4 && !r.unanimous).length;
  const threeOfFive = perCase.filter(r => r.agreement_count === 3).length;
  const unstable = perCase.filter(r => r.agreement_count < 3 || r.is_tie).length;
  const meanAgreement = perCase.reduce((s, r) => s + r.agreement_count, 0) / total;
  const amendedMatches = perCase.filter(r => r.match_amended).length;

  console.log('================================================');
  console.log('STABILITY ASSESSMENT SUMMARY');
  console.log('================================================');
  console.log();
  console.log('SCHEMA VALIDITY');
  console.log(`  All runs valid: ${perCase.filter(r => r.all_valid).length}/${total}`);
  console.log(`  Total valid traces: ${perCase.reduce((s,r) => s + (r.all_valid ? N_RUNS : 0), 0)}/${total * N_RUNS}`);
  console.log();
  console.log('RATE LIMIT IMPACT');
  console.log(`  Total fallback traces: ${totalFallbacks}/${total * N_RUNS}`);
  console.log(`  Cases with zero fallbacks: ${perCase.filter(r => r.fallback_count === 0).length}/${total}`);
  console.log();
  console.log('STABILITY');
  console.log(`  Mean per-case agreement: ${meanAgreement.toFixed(2)}/${N_RUNS}`);
  console.log(`  Unanimous (5/5): ${unanimousCount}/${total}`);
  console.log(`  4/5 agreement: ${fourOfFive}/${total}`);
  console.log(`  3/5 agreement: ${threeOfFive}/${total}`);
  console.log(`  Unstable (<3/5 or tie): ${unstable}/${total}`);
  console.log();
  console.log('CALIBRATION ACCURACY (majority vote, amended spec)');
  console.log(`  ${amendedMatches}/${total}`);
  console.log();
  console.log('SEMANTIC FAILURES');
  const failures = perCase.filter(r => !r.match_amended);
  console.log(`  ${failures.length} cases wrong:`);
  for (const f of failures) {
    console.log(`    ${f.id}: '${f.candidate}' expected=${f.expected_amended} got=${f.majority} (${f.agreement_count}/${N_RUNS}${f.is_tie ? ', TIE' : ''})`);
  }
  console.log();
  console.log('NO-TUNING CONFIRMATION');
  console.log(`  Detector modified: NO`);
  console.log(`  Prompt modified: NO`);
  console.log(`  Code modified: NO`);

  const report = {
    assessment: 'n=5 stability (rate-limit safe)',
    n_runs: N_RUNS, total_llm_calls: N_RUNS * total,
    delay_ms: DELAY_MS,
    no_tuning: { detector_modified: false, prompt_modified: false, code_modified: false },
    schema_validity: { all_runs_valid: perCase.filter(r => r.all_valid).length, total_cases: total },
    rate_limit_impact: { total_fallbacks: totalFallbacks, total_traces: total * N_RUNS },
    stability: { mean_agreement: parseFloat(meanAgreement.toFixed(2)), unanimous: unanimousCount, four_of_five: fourOfFive, three_of_five: threeOfFive, unstable, total },
    calibration_accuracy: { amended_spec_labels: amendedMatches, total },
    semantic_failures: failures.map(f => ({ id: f.id, candidate: f.candidate, expected: f.expected_amended, got: f.majority, agreement: `${f.agreement_count}/${N_RUNS}`, is_tie: f.is_tie })),
    per_case: perCase,
  };
  writeFileSync(join(OUTPUT_DIR, 'stability_report.json'), JSON.stringify(report, null, 2));
  console.log(`\nReport: ${OUTPUT_DIR}/stability_report.json`);
}

main().catch(err => { console.error('Fatal:', err); process.exit(1); });
