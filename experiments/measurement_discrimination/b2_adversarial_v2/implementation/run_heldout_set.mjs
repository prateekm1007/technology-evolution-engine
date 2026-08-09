#!/usr/bin/env node
/**
 * run_heldout_set.mjs — Test harness for the sealed held-out set
 *
 * Per §7.4/§7.5 of REPAIR_SPEC.md:
 *   - Accepts a path to a held-out fixture (provided by auditor at run time)
 *   - Runs the detector on each case
 *   - Validates each trace against b2-trace-v3 schema
 *   - Reports per-case results and summary
 *   - If the fixture contains expected labels, reports matches; otherwise
 *     reports only detector labels (auditor adjudicates)
 *
 * This harness was developed WITHOUT access to held-out content.
 * The implementer does not see the held-out cases, labels, or rationales.
 *
 * Usage:
 *   node run_heldout_set.mjs <heldout_fixture.json> [n_runs]
 *
 * The fixture format is expected to match test_fixture.json:
 *   { source_a, source_b, cases: [{id, candidate, ...}] }
 * (Per-case source_a/source_b override is supported if present.)
 */
import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join, basename } from 'path';
import { detectOnce, detect, FROZEN_CONFIG } from './b2_detector.mjs';
import { validateTrace } from './b2_trace_validator.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function main() {
  const fixturePath = process.argv[2];
  const nArg = parseInt(process.argv[3] || '5', 10);
  const n = nArg > 0 ? nArg : 5;

  if (!fixturePath) {
    console.error('Usage: run_heldout_set.mjs <heldout_fixture.json> [n_runs]');
    console.error('  n_runs default: 5 (per §5.7 requirement 4 — majority vote)');
    process.exit(1);
  }

  console.log('B-2 Held-Out Set Evaluation');
  console.log('============================');
  console.log(`Fixture: ${fixturePath}`);
  console.log(`Model: ${FROZEN_CONFIG.model_identifier}`);
  console.log(`Runs per case: ${n} (majority vote per §5.7 req 4)`);
  console.log();

  const fixture = JSON.parse(readFileSync(fixturePath, 'utf-8'));

  // Support multiple source pairs in the held-out set
  // Format option 1: { source_a, source_b, cases: [...] }  (single pair)
  // Format option 2: { pairs: [{ id, source_a, source_b, cases: [...] }] }  (multiple pairs)
  let pairs;
  if (fixture.pairs && Array.isArray(fixture.pairs)) {
    pairs = fixture.pairs;
  } else {
    pairs = [{
      id: 'default',
      source_a: fixture.source_a,
      source_b: fixture.source_b,
      cases: fixture.cases || [],
    }];
  }

  const fixtureBasename = basename(fixturePath).replace(/\.json$/, '');
  const outputDir = join(__dirname, 'heldout_results', fixtureBasename);
  mkdirSync(outputDir, { recursive: true });

  const allResults = [];

  for (const pair of pairs) {
    console.log(`\nSource Pair: ${pair.id || 'default'}`);
    console.log(`  A: ${(pair.source_a || '').substring(0, 80)}...`);
    console.log(`  B: ${(pair.source_b || '').substring(0, 80)}...`);
    console.log(`  Cases: ${pair.cases.length}`);
    console.log();

    for (const testCase of pair.cases) {
      const params = {
        id: testCase.id,
        candidate: testCase.candidate,
        source_a: testCase.source_a || pair.source_a,
        source_b: testCase.source_b || pair.source_b,
      };

      console.log(`[${testCase.id}] ${testCase.candidate}`);

      let trace, labelDistribution = null, isTie = false;
      if (n === 1) {
        trace = await detectOnce(params);
      } else {
        const result = await detect(params, n);
        trace = result.canonical_trace;
        labelDistribution = result.label_distribution;
        isTie = result.is_tie;
        console.log(`  label distribution: ${JSON.stringify(labelDistribution)}`);
        if (isTie) {
          console.log(`  WARNING: tie detected — counted as failure`);
        }
      }

      const detectorLabel = trace.classification?.label || 'UNKNOWN';
      const detectorState = trace.classification?.iss_state || 'UNKNOWN';

      // Check if expected label is provided (may be absent in blind mode)
      const expectedLabel = testCase.expected_label || null;
      const match = expectedLabel ? (detectorLabel === expectedLabel) : null;

      const validation = validateTrace(trace);

      const matchStr = match === null ? 'BLIND' : (match ? '✓' : '✗');
      console.log(`  detector: ${detectorLabel} (${detectorState}) ${matchStr}`);
      if (expectedLabel) {
        console.log(`  expected: ${expectedLabel}`);
      }
      if (!validation.valid) {
        console.log(`  validation: ${validation.errors.length} error(s)`);
        for (const err of validation.errors.slice(0, 3)) {
          console.log(`    - ${err}`);
        }
      }
      console.log();

      allResults.push({
        pair_id: pair.id || 'default',
        id: testCase.id,
        candidate: testCase.candidate,
        expected_label: expectedLabel,
        detector_label: detectorLabel,
        iss_state: detectorState,
        match,
        is_tie: isTie,
        label_distribution: labelDistribution,
        trace_valid: validation.valid,
        validation_errors: validation.errors,
        trace,
      });

      // Save individual trace
      writeFileSync(
        join(outputDir, `${testCase.id}.trace.json`),
        JSON.stringify(trace, null, 2)
      );
    }
  }

  // Summary
  const total = allResults.length;
  const labeled = allResults.filter(r => r.match !== null);
  const matches = labeled.filter(r => r.match).length;
  const ties = allResults.filter(r => r.is_tie).length;
  const validTraces = allResults.filter(r => r.trace_valid).length;

  console.log('\n============================');
  console.log('SUMMARY');
  console.log('============================');
  console.log(`Total cases: ${total}`);
  console.log(`Labeled cases: ${labeled.length}`);
  console.log(`Label matches: ${matches}/${labeled.length}`);
  console.log(`Ties: ${ties}`);
  console.log(`Valid traces: ${validTraces}/${total}`);
  console.log();

  // TP/TN/FP/FN (only for labeled cases)
  if (labeled.length > 0) {
    let TP = 0, TN = 0, FP = 0, FN = 0;
    for (const r of labeled) {
      const expectedReject = (r.expected_label === 'REJECT');
      const detectorReject = (r.detector_label === 'REJECT');
      if (expectedReject && detectorReject) TP++;
      else if (!expectedReject && !detectorReject) TN++;
      else if (!expectedReject && detectorReject) FP++;
      else if (expectedReject && !detectorReject) FN++;
    }
    console.log('TP/TN/FP/FN (REJECT = positive class):');
    console.log(`  TP=${TP}  TN=${TN}  FP=${FP}  FN=${FN}`);
    const precision = TP + FP > 0 ? (TP / (TP + FP)).toFixed(3) : 'N/A';
    const recall = TP + FN > 0 ? (TP / (TP + FN)).toFixed(3) : 'N/A';
    const fpr = FP + TN > 0 ? (FP / (FP + TN)).toFixed(3) : 'N/A';
    const fnr = TP + FN > 0 ? (FN / (FN + TP)).toFixed(3) : 'N/A';
    console.log(`  precision=${precision}  recall=${recall}  FPR=${fpr}  FNR=${fnr}`);
    console.log();
  }

  // Save summary
  const summary = {
    fixture: fixturePath,
    model: FROZEN_CONFIG.model_identifier,
    n_runs: n,
    total_cases: total,
    labeled_cases: labeled.length,
    label_matches: matches,
    ties,
    valid_traces: validTraces,
    tp_tn_fp_fn: labeled.length > 0 ? { TP, TN, FP, FN } : null,
    results: allResults.map(r => ({
      pair_id: r.pair_id,
      id: r.id,
      candidate: r.candidate,
      expected_label: r.expected_label,
      detector_label: r.detector_label,
      iss_state: r.iss_state,
      match: r.match,
      is_tie: r.is_tie,
      trace_valid: r.trace_valid,
      validation_error_count: r.validation_errors.length,
    })),
  };

  writeFileSync(
    join(outputDir, 'summary.json'),
    JSON.stringify(summary, null, 2)
  );

  console.log(`Traces saved to: ${outputDir}/`);
  console.log(`Summary saved to: ${outputDir}/summary.json`);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
