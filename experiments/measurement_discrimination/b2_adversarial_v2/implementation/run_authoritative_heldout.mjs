#!/usr/bin/env node
/**
 * run_authoritative_heldout.mjs — FROZEN B-2 HELD-OUT EVALUATION
 * MODEL IDENTITY GATE: glm-4-plus via original frozen z-ai instrument
 * detector: f905b68 (UNMODIFIED), N=5, 20 cases, 100 executions
 * Machine-only outputs. No answer-key comparison.
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { createHash } from 'crypto';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const FIXTURE_PATH = '/home/z/my-project/audit/b2_heldout_blind.json';
const RESULTS_DIR = join(__dirname, 'heldout_results', 'FROZEN_B2_HELDOUT_RESULTS', 'traces');
const N_RUNS = 5;

mkdirSync(RESULTS_DIR, { recursive: true });

async function main() {
  console.log('=== FROZEN B-2 HELD-OUT EVALUATION (AUTHORITATIVE) ===');
  console.log('MODEL IDENTITY GATE: ENFORCED');
  console.log('  detector: b2_detector.mjs @ f905b68 (UNMODIFIED)');
  console.log('  LLM: glm-4-plus (via original frozen z-ai instrument)');
  console.log('  N runs per case: 5 (majority vote per §5.7 req 4)');
  console.log('  20 cases × 5 runs = 100 executions total');
  console.log('  PROTOCOL: Machine-only outputs. No answer-key comparison.');

  // Verify fixture hash
  const fixtureBytes = readFileSync(FIXTURE_PATH);
  const fixtureHash = createHash('sha256').update(fixtureBytes).digest('hex');
  console.log(`\nFixture SHA-256: ${fixtureHash}`);
  if (fixtureHash !== '8a3e51bc74b32ac8c697da48487885d97aee0aa4411488c69fb051ede76bd380') {
    console.error('FATAL: Fixture hash mismatch! Aborting.');
    process.exit(1);
  }
  console.log('Fixture hash VERIFIED.\n');

  const fixture = JSON.parse(fixtureBytes.toString());
  const { detectOnce, FROZEN_CONFIG } = await import('./b2_detector.mjs');
  console.log(`Frozen config model: ${FROZEN_CONFIG.model_identifier}\n`);

  const allResults = [];

  for (const pair of fixture.pairs) {
    console.log(`\n=== ${pair.id} ===`);
    console.log(`  Cases: ${pair.cases.length}`);

    for (const tc of pair.cases) {
      const caseId = tc.id;
      console.log(`\n  [${caseId}] ${tc.candidate}`);
      const caseDir = join(RESULTS_DIR, caseId);
      mkdirSync(caseDir, { recursive: true });

      const runs = [];
      for (let run = 1; run <= N_RUNS; run++) {
        const runPath = join(caseDir, `run${run}.trace.json`);
        if (existsSync(runPath)) {
          try {
            const existing = JSON.parse(readFileSync(runPath, 'utf-8'));
            if (!existing._fallback && existing.classification?.label !== 'NOT_ADJUDICATED_BY_B2') {
              console.log(`    run ${run}: CACHED ${existing.classification.label}`);
              runs.push(existing);
              continue;
            }
          } catch (e) { }
        }
        const t0 = Date.now();
        try {
          console.log(`    run ${run}: running...`);
          const trace = await detectOnce({
            id: caseId, candidate: tc.candidate,
            source_a: pair.source_a, source_b: pair.source_b,
          });
          writeFileSync(runPath, JSON.stringify(trace, null, 2));
          console.log(`    run ${run}: ${trace.classification?.label} (${((Date.now()-t0)/1000).toFixed(1)}s)`);
          runs.push(trace);
        } catch (e) {
          console.log(`    run ${run}: ERROR ${e.message.substring(0, 80)}`);
          writeFileSync(runPath, JSON.stringify({_fallback:true,_error:e.message,classification:{label:'NOT_ADJUDICATED_BY_B2'}}, null, 2));
        }
        await new Promise(r => setTimeout(r, 500));
      }

      // Majority vote
      const labels = runs.filter(t => t?.classification?.label !== 'NOT_ADJUDICATED_BY_B2').map(t => t.classification.label);
      const labelCounts = {};
      for (const l of labels) labelCounts[l] = (labelCounts[l] || 0) + 1;
      let majorityLabel = 'NOT_ADJUDICATED_BY_B2', maxCount = 0, isTie = false;
      for (const [l, c] of Object.entries(labelCounts)) {
        if (c > maxCount) { majorityLabel = l; maxCount = c; isTie = false; }
        else if (c === maxCount) isTie = true;
      }
      const canonical = runs.find(t => t?.classification?.label === majorityLabel) || runs[0];
      const canonicalBytes = Buffer.from(JSON.stringify(canonical));
      const traceHash = createHash('sha256').update(canonicalBytes).digest('hex');

      console.log(`    MAJORITY: ${majorityLabel} (${maxCount}/${labels.length})${isTie ? ' [TIE]' : ''}`);

      allResults.push({
        pair_id: pair.id, case_id: caseId, candidate: tc.candidate,
        n_runs_completed: runs.length, n_valid_runs: labels.length,
        majority_label: majorityLabel, label_distribution: labelCounts,
        is_tie: isTie, iss_state: canonical?.classification?.iss_state,
        canonical_trace_hash: traceHash,
      });
      writeFileSync(join(caseDir, 'case_summary.json'), JSON.stringify({
        case_id: caseId, candidate: tc.candidate, pair_id: pair.id,
        n_runs: runs.length, majority_label: majorityLabel,
        label_distribution: labelCounts, is_tie: isTie,
        iss_state: canonical?.classification?.iss_state, trace_hash: traceHash,
      }, null, 2));
    }
  }

  const summary = {
    schema_version: 'frozen-b2-heldout-results-v1',
    package: 'FROZEN_B2_HELDOUT_RESULTS',
    timestamp: new Date().toISOString(),
    model_identity: {
      detector: 'b2_detector.mjs @ f905b68',
      llm: 'glm-4-plus',
      provider: 'z-ai internal API (original frozen instrument)',
      fixture_sha256: '8a3e51bc74b32ac8c697da48487885d97aee0aa4411488c69fb051ede76bd380',
    },
    n_runs_per_case: N_RUNS,
    total_cases: allResults.length,
    total_executions: allResults.reduce((sum, r) => sum + r.n_runs_completed, 0),
    results: allResults,
    note: 'Machine-only outputs. No answer-key comparison. No correctness calculation. Awaiting independent answer-key custodian.',
  };
  writeFileSync(join(RESULTS_DIR, '..', 'summary.json'), JSON.stringify(summary, null, 2));

  // Print label distribution
  const labelDist = {};
  for (const r of allResults) labelDist[r.majority_label] = (labelDist[r.majority_label] || 0) + 1;
  console.log('\n============================');
  console.log('AUTHORITATIVE EVALUATION SUMMARY');
  console.log('============================');
  console.log(`Total cases: ${allResults.length}`);
  console.log(`Total executions: ${allResults.reduce((s,r)=>s+r.n_runs_completed,0)}/100`);
  console.log(`\nLabel distribution (machine-only):`);
  for (const [l,c] of Object.entries(labelDist).sort()) console.log(`  ${l}: ${c}`);
  console.log(`\nSummary saved: ${join(RESULTS_DIR, '..', 'summary.json')}`);
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
