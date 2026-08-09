#!/usr/bin/env node
/**
 * run_public_set.mjs — Test harness for the public 13-case calibration set
 *
 * Per §7.4 of REPAIR_SPEC.md:
 *   - Uses the public adversarial set (test_fixture.json) as calibration
 *   - Runs the detector on each case
 *   - Validates each trace against b2-trace-v3 schema
 *   - Reports per-case results and summary
 *
 * This harness does NOT access any held-out material.
 */
import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { detectOnce, FROZEN_CONFIG } from './b2_detector.mjs';
import { validateTrace } from './b2_trace_validator.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const FIXTURE_PATH = join(__dirname, '..', 'test_fixture.json');
const OUTPUT_DIR = join(__dirname, 'public_set_results');

async function main() {
  const nArg = parseInt(process.argv[2] || '1', 10);
  const n = nArg > 0 ? nArg : 1;

  console.log('B-2 Public Set Calibration Run');
  console.log('================================');
  console.log(`Model: ${FROZEN_CONFIG.model_identifier}`);
  console.log(`Runs per case: ${n}`);
  console.log();

  const fixture = JSON.parse(readFileSync(FIXTURE_PATH, 'utf-8'));
  const source_a = fixture.source_a;
  const source_b = fixture.source_b;

  mkdirSync(OUTPUT_DIR, { recursive: true });

  const results = [];

  for (const testCase of fixture.cases) {
    const params = {
      id: testCase.id,
      candidate: testCase.candidate,
      source_a,
      source_b,
    };

    console.log(`[${testCase.id}] ${testCase.candidate}`);
    console.log(`  expected: ${testCase.expected_label}`);

    let trace;
    if (n === 1) {
      trace = await detectOnce(params);
    } else {
      // Multiple runs with majority vote
      const { detect } = await import('./b2_detector.mjs');
      const result = await detect(params, n);
      trace = result.canonical_trace;
      console.log(`  label distribution: ${JSON.stringify(result.label_distribution)}`);
      if (result.is_tie) {
        console.log(`  WARNING: tie detected`);
      }
    }

    const detectorLabel = trace.classification?.label || 'UNKNOWN';
    const match = detectorLabel === testCase.expected_label;

    // Validate the trace
    const validation = validateTrace(trace);

    console.log(`  detector: ${detectorLabel} ${match ? '✓' : '✗'}`);
    if (!validation.valid) {
      console.log(`  validation: ${validation.errors.length} error(s)`);
      for (const err of validation.errors.slice(0, 3)) {
        console.log(`    - ${err}`);
      }
      if (validation.errors.length > 3) {
        console.log(`    ... and ${validation.errors.length - 3} more`);
      }
    }
    console.log();

    results.push({
      id: testCase.id,
      category: testCase.category,
      candidate: testCase.candidate,
      expected_label: testCase.expected_label,
      detector_label: detectorLabel,
      match,
      iss_state: trace.classification?.iss_state,
      trace_valid: validation.valid,
      validation_errors: validation.errors,
      trace,
    });

    // Save individual trace
    writeFileSync(
      join(OUTPUT_DIR, `${testCase.id}.trace.json`),
      JSON.stringify(trace, null, 2)
    );
  }

  // Summary
  const total = results.length;
  const matches = results.filter(r => r.match).length;
  const validTraces = results.filter(r => r.trace_valid).length;

  console.log('================================');
  console.log('SUMMARY');
  console.log('================================');
  console.log(`Total cases: ${total}`);
  console.log(`Label matches: ${matches}/${total}`);
  console.log(`Valid traces: ${validTraces}/${total}`);
  console.log();

  // By category
  const byCategory = {};
  for (const r of results) {
    const cat = r.category;
    if (!byCategory[cat]) {
      byCategory[cat] = { total: 0, match: 0, valid: 0 };
    }
    byCategory[cat].total++;
    if (r.match) byCategory[cat].match++;
    if (r.trace_valid) byCategory[cat].valid++;
  }

  console.log('BY CATEGORY');
  console.log('--------------------------------');
  for (const [cat, data] of Object.entries(byCategory)) {
    console.log(`  ${cat}`);
    console.log(`    match: ${data.match}/${data.total}`);
    console.log(`    valid: ${data.valid}/${data.total}`);
  }
  console.log();

  // Per-case detail
  console.log('PER-CASE DETAIL');
  console.log('--------------------------------');
  for (const r of results) {
    const status = r.match ? 'MATCH' : 'MISMATCH';
    const valid = r.trace_valid ? 'VALID' : 'INVALID';
    console.log(`  [${status}] [${valid}] ${r.id}: '${r.candidate}'`);
    console.log(`    expected=${r.expected_label}, detector=${r.detector_label}, iss_state=${r.iss_state}`);
  }

  // Save summary
  const summary = {
    model: FROZEN_CONFIG.model_identifier,
    n_runs: n,
    total_cases: total,
    label_matches: matches,
    valid_traces: validTraces,
    by_category: byCategory,
    results: results.map(r => ({
      id: r.id,
      category: r.category,
      candidate: r.candidate,
      expected_label: r.expected_label,
      detector_label: r.detector_label,
      match: r.match,
      iss_state: r.iss_state,
      trace_valid: r.trace_valid,
      validation_error_count: r.validation_errors.length,
    })),
  };

  writeFileSync(
    join(OUTPUT_DIR, 'summary.json'),
    JSON.stringify(summary, null, 2)
  );

  console.log();
  console.log(`Traces saved to: ${OUTPUT_DIR}/`);
  console.log(`Summary saved to: ${OUTPUT_DIR}/summary.json`);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
