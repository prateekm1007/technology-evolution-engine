#!/usr/bin/env node
// run_single_case.mjs — Run n=5 for a single case (resumable approach)
// Usage: node run_single_case.mjs <case_id>
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { detectOnce } from './b2_detector.mjs';

const caseId = process.argv[2];
if (!caseId) { console.error('Usage: node run_single_case.mjs <case_id>'); process.exit(1); }

const fixture = JSON.parse(readFileSync('../test_fixture.json', 'utf-8'));
const tc = fixture.cases.find(c => c.id === caseId);
if (!tc) { console.error(`Case ${caseId} not found`); process.exit(1); }

const params = { id: tc.id, candidate: tc.candidate, source_a: fixture.source_a, source_b: fixture.source_b };
const sleep = ms => new Promise(r => setTimeout(r, ms));

console.log(`[${caseId}] ${tc.candidate}`);
for (let i = 1; i <= 5; i++) {
  const path = `stability_results/${caseId}.run${i}.trace.json`;
  // Skip if already done and not a fallback
  if (existsSync(path)) {
    const existing = JSON.parse(readFileSync(path, 'utf-8'));
    if (!existing._fallback) {
      console.log(`  run ${i}/5: cached (${existing.classification?.label})`);
      continue;
    }
  }
  const trace = await detectOnce(params);
  writeFileSync(path, JSON.stringify(trace, null, 2));
  const label = trace.classification?.label || 'UNKNOWN';
  console.log(`  run ${i}/5: ${label}${trace._fallback ? ' [FALLBACK]' : ''}`);
  if (i < 5) await sleep(12000);
}
console.log('Done.');
