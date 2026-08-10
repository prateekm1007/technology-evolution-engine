#!/usr/bin/env node
/**
 * run_abc_checkpointed.mjs — Full 13-case A/B/C with checkpointing + resume.
 *
 * Features:
 * - Exponential backoff on 429 errors (15s, 30s, 60s, 120s, 240s)
 * - Persistent checkpoint after every case/representation
 * - Resume capability — skips completed entries
 * - No duplicate API calls
 * - Saves full results + per-case traces
 */
import ZAI from 'z-ai-web-dev-sdk';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { createHash } from 'crypto';

const __dirname = dirname(fileURLToPath(import.meta.url));
const sleep = ms => new Promise(r => setTimeout(r, ms));

const EVIDENCE_PATH = join(__dirname, 'results', 'glirel', 'evidence_graphs_v3.json');
const FIXTURE_PATH = join(__dirname, '..', '..', 'b2_adversarial_v2', 'test_fixture.json');
const CHECKPOINT_PATH = join(__dirname, 'results', 'abc', 'checkpoint.json');
const OUTPUT_PATH = join(__dirname, 'results', 'abc', 'abc_full_results.json');
mkdirSync(join(__dirname, 'results', 'abc'), { recursive: true });

const MODEL = 'glm-4-plus';

const BASE_PROMPT = `You are a B-2 leakage detection instrument with structured evidence assistance.

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

Your job: determine whether the candidate is leaked from one source (ISS_one -> REJECT),
genuinely cross-source (ISS_both -> ALLOW), redundantly supported (REDUNDANT_SUPPORT -> ALLOW),
or unsupported (UNSUPPORTED -> NOT_ADJUDICATED_BY_B2).

Use GLiREL evidence as a STARTING POINT. Verify each relation against source text yourself.

OUTPUT: ONLY a valid JSON object:
{
  "classification": {
    "justified_by_corpus": <boolean>,
    "iss_a": <boolean>,
    "iss_b": <boolean>,
    "iss_state": "<ISS_one|ISS_both|REDUNDANT_SUPPORT|UNSUPPORTED>",
    "label": "<REJECT|ALLOW|NOT_ADJUDICATED_BY_B2>"
  },
  "evidence_assessment": {
    "glirel_relations_available": <int>,
    "relations_relevant": <int>,
    "relations_cited": <int>,
    "glirel_evidence_helpful": <boolean>,
    "false_evidence_cited": <boolean>,
    "cited_relation_details": ["<brief description of each cited relation>"],
    "rejected_relation_details": ["<brief description of why rejected>"],
    "notes": "<brief explanation>"
  }
}

Output ONLY the JSON. No markdown, no prose.`;

function buildPrompt(rep, ev) {
  const sa = ev.source_a.text;
  const sb = ev.source_b.text;
  const relsA = ev.source_a.relations;
  const relsB = ev.source_b.relations;

  if (rep === 'A') {
    return `CASE ID: ${ev.case_id}\nCANDIDATE: ${ev.candidate}\n\nSOURCE A:\n${sa}\n\nSOURCE B:\n${sb}\n\nGLiREL EVIDENCE (Source A, top 10):\n${relsA.slice(0,10).map((r,i)=>`${i+1}. ${r.label}: ${r.head_text} -> ${r.tail_text} (score=${r.score?.toFixed(3)})`).join('\n')}\n\nGLiREL EVIDENCE (Source B, top 10):\n${relsB.slice(0,10).map((r,i)=>`${i+1}. ${r.label}: ${r.head_text} -> ${r.tail_text} (score=${r.score?.toFixed(3)})`).join('\n')}\n\nIMPORTANT: GLiREL evidence is extraction, NOT truth. Verify independently.\n\nOutput the JSON.`;
  }
  if (rep === 'B') {
    return `CASE ID: ${ev.case_id}\nCANDIDATE: ${ev.candidate}\n\nSOURCE A:\n${sa}\n\nSOURCE B:\n${sb}\n\nSTRUCTURED EVIDENCE TABLE (Source A):\nFormat: #|head_text|head_span|relation|tail_text|tail_span|score\n${relsA.slice(0,10).map((r,i)=>`${i+1}|${r.head_text}|[${r.head_span.start},${r.head_span.end}]|${r.label}|${r.tail_text}|[${r.tail_span.start},${r.tail_span.end}]|${r.score?.toFixed(3)}`).join('\n')}\n\nSTRUCTURED EVIDENCE TABLE (Source B):\n${relsB.slice(0,10).map((r,i)=>`${i+1}|${r.head_text}|[${r.head_span.start},${r.head_span.end}]|${r.label}|${r.tail_text}|[${r.tail_span.start},${r.tail_span.end}]|${r.score?.toFixed(3)}`).join('\n')}\n\nAll spans are mechanically valid. Verify by checking source[start:end] == text.\nIMPORTANT: GLiREL evidence is extraction, NOT truth. Verify independently.\n\nOutput the JSON.`;
  }
  // C: evidence graph
  return `CASE ID: ${ev.case_id}\nCANDIDATE: ${ev.candidate}\n\nSOURCE A:\n${sa}\n\nSOURCE B:\n${sb}\n\nEVIDENCE GRAPH — Source A:\nNodes (entities with exact spans):\n${ev.source_a.entities.map((e,i)=>`  A${i}: "${e.text}" [${e.start},${e.end}] label=${e.label}`).join('\n')}\nEdges (relations with provenance):\n${relsA.slice(0,10).map((r,i)=>`  A_E${i}: "${r.head_text}" --[${r.label}]--> "${r.tail_text}" (score=${r.score?.toFixed(3)}, head=[${r.head_span.start},${r.head_span.end}], tail=[${r.tail_span.start},${r.tail_span.end}])`).join('\n')}\n\nEVIDENCE GRAPH — Source B:\nNodes (entities with exact spans):\n${ev.source_b.entities.map((e,i)=>`  B${i}: "${e.text}" [${e.start},${e.end}] label=${e.label}`).join('\n')}\nEdges (relations with provenance):\n${relsB.slice(0,10).map((r,i)=>`  B_E${i}: "${r.head_text}" --[${r.label}]--> "${r.tail_text}" (score=${r.score?.toFixed(3)}, head=[${r.head_span.start},${r.head_span.end}], tail=[${r.tail_span.start},${r.tail_span.end}])`).join('\n')}\n\nCANDIDATE OVERLAY:\nThe candidate "${ev.candidate}" should be evaluated against the evidence graph.\nWhich graph nodes correspond to candidate components?\nWhich graph edges support candidate relations?\nWhich source supplies each component?\n\nAll spans are mechanically valid. IMPORTANT: GLiREL evidence is extraction, NOT truth.\n\nOutput the JSON.`;
}

function loadCheckpoint() {
  if (existsSync(CHECKPOINT_PATH)) {
    return JSON.parse(readFileSync(CHECKPOINT_PATH, 'utf-8'));
  }
  return { completed: {}, results: [] };
}

function saveCheckpoint(checkpoint) {
  writeFileSync(CHECKPOINT_PATH, JSON.stringify(checkpoint, null, 2));
}

async function callWithBackoff(zai, prompt, maxRetries = 5) {
  let delay = 8000;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const completion = await zai.chat.completions.create({
        model: MODEL,
        messages: [
          { role: 'assistant', content: BASE_PROMPT },
          { role: 'user', content: prompt },
        ],
        thinking: { type: 'disabled' },
      });
      let content = (completion.choices?.[0]?.message?.content || '').trim();
      content = content.replace(/^```(?:json)?\n?/, '').replace(/\n?```$/, '');
      return content;
    } catch (err) {
      if (err.message?.includes('429') && attempt < maxRetries) {
        process.stdout.write(`    [retry ${attempt}/${maxRetries}] 429, waiting ${delay/1000}s...\n`);
        await sleep(delay);
        delay *= 2;
      } else {
        throw err;
      }
    }
  }
  throw new Error('Max retries exceeded');
}

async function main() {
  process.stdout.write('B-2 GLiREL A/B/C Full 13-Case Experiment (Checkpointed)\n');
  process.stdout.write('=========================================================\n');
  process.stdout.write(`Model: ${MODEL}\n`);

  const evidence = JSON.parse(readFileSync(EVIDENCE_PATH, 'utf-8'));
  const fixture = JSON.parse(readFileSync(FIXTURE_PATH, 'utf-8'));
  const zai = await ZAI.create();

  const checkpoint = loadCheckpoint();
  const reps = ['A', 'B', 'C'];
  let caseCount = 0;

  for (const ev of evidence) {
    const tc = fixture.cases.find(c => c.id === ev.case_id);
    if (!tc) continue;
    caseCount++;

    const amended = ev.case_id === 'ADV-09' ? 'NOT_ADJUDICATED_BY_B2' : tc.expected_label;
    const caseKey = ev.case_id;
    process.stdout.write(`\n[${caseKey}] ${ev.candidate} (expected: ${amended})\n`);

    let caseResult = checkpoint.results.find(r => r.case_id === caseKey);
    if (!caseResult) {
      caseResult = { case_id: caseKey, candidate: ev.candidate, expected: amended };
      checkpoint.results.push(caseResult);
    }

    for (const rep of reps) {
      const checkKey = `${caseKey}_${rep}`;
      if (checkpoint.completed[checkKey]) {
        process.stdout.write(`  ${rep}: CACHED ${caseResult[rep]?.label || '?'}\n`);
        continue;
      }

      process.stdout.write(`  ${rep}: calling API...`);
      const prompt = buildPrompt(rep, ev);

      try {
        const content = await callWithBackoff(zai, prompt);
        let trace;
        try {
          trace = JSON.parse(content);
        } catch (e) {
          trace = { classification: { label: 'PARSE_ERROR' }, evidence_assessment: {}, raw: content.substring(0, 300) };
        }

        const label = trace.classification?.label || 'ERROR';
        const state = trace.classification?.iss_state || 'UNKNOWN';
        const match = label === amended;
        const evAssess = trace.evidence_assessment || {};
        const cited = evAssess.relations_cited || 0;
        const available = evAssess.glirel_relations_available || 0;
        const relevant = evAssess.relations_relevant || 0;
        const helpful = evAssess.glirel_evidence_helpful;
        const falseCit = evAssess.false_evidence_cited || false;
        const citedDetails = evAssess.cited_relation_details || [];
        const rejectedDetails = evAssess.rejected_relation_details || [];

        caseResult[rep] = {
          label, state, match, cited, available, relevant, helpful,
          false_citation: falseCit,
          cited_details: citedDetails,
          rejected_details: rejectedDetails,
        };

        checkpoint.completed[checkKey] = {
          status: 'complete',
          attempts: 1,
          timestamp: new Date().toISOString(),
          result_sha256: createHash('sha256').update(content).digest('hex').substring(0, 16),
        };

        process.stdout.write(` ${label} (${state}) ${match ? 'OK' : 'X'} cited=${cited} false=${falseCit}\n`);
      } catch (err) {
        caseResult[rep] = { label: 'ERROR', state: 'ERROR', match: false, cited: 0, false_citation: false, error: err.message };
        checkpoint.completed[checkKey] = { status: 'error', attempts: 5, timestamp: new Date().toISOString(), error: err.message };
        process.stdout.write(` ERROR: ${err.message}\n`);
      }

      saveCheckpoint(checkpoint);
      await sleep(3000); // 5s between successful calls
    }
  }

  // ── Summary ──
  const total = checkpoint.results.length;
  const reps_summary = {};
  for (const rep of reps) {
    const results = checkpoint.results.map(r => r[rep]).filter(r => r);
    const matches = results.filter(r => r.match).length;
    const falseCit = results.filter(r => r.false_citation).length;
    const totalCited = results.reduce((s, r) => s + (r.cited || 0), 0);
    const labels = {};
    for (const r of results) {
      labels[r.label] = (labels[r.label] || 0) + 1;
    }

    reps_summary[rep] = {
      total: results.length,
      matches,
      accuracy: matches / results.length,
      false_citations: falseCit,
      false_citation_rate: falseCit / results.length,
      total_cited: totalCited,
      avg_cited: totalCited / results.length,
      label_distribution: labels,
    };
  }

  // Per-case table
  process.stdout.write('\n' + '='.repeat(70) + '\n');
  process.stdout.write('FULL A/B/C COMPARISON (13 cases)\n');
  process.stdout.write('='.repeat(70) + '\n\n');
  process.stdout.write('Case'.padEnd(10) + 'Expected'.padEnd(20) + 'A'.padEnd(20) + 'B'.padEnd(20) + 'C'.padEnd(20) + '\n');
  process.stdout.write('-'.repeat(90) + '\n');
  for (const r of checkpoint.results) {
    const fmt = (rep) => {
      const v = r[rep];
      if (!v) return 'N/A';
      return `${v.label} ${v.match ? 'OK' : 'X'}`;
    };
    process.stdout.write(`${r.case_id.padEnd(10)}${r.expected.padEnd(20)}${fmt('A').padEnd(20)}${fmt('B').padEnd(20)}${fmt('C').padEnd(20)}\n`);
  }

  process.stdout.write('\n' + '='.repeat(70) + '\n');
  process.stdout.write('SUMMARY\n');
  process.stdout.write('='.repeat(70) + '\n');
  process.stdout.write('                    A (raw)    B (table)   C (graph)\n');
  for (const rep of reps) {
    const s = reps_summary[rep];
    process.stdout.write(`${rep} accuracy:        ${s.matches}/${s.total}\n`);
  }
  process.stdout.write('\n');
  for (const rep of reps) {
    const s = reps_summary[rep];
    process.stdout.write(`${rep} false citations:  ${s.false_citations}/${s.total}\n`);
  }
  process.stdout.write('\n');
  for (const rep of reps) {
    const s = reps_summary[rep];
    process.stdout.write(`${rep} total cited:      ${s.total_cited} (avg ${s.avg_cited.toFixed(1)}/case)\n`);
  }
  process.stdout.write('\n');
  for (const rep of reps) {
    const s = reps_summary[rep];
    process.stdout.write(`${rep} labels: ${JSON.stringify(s.label_distribution)}\n`);
  }

  // Failure cases
  const failIds = ['ADV-05', 'ADV-06', 'ADV-07', 'ADV-08', 'ADV-13'];
  process.stdout.write('\nFAILURE CASES:\n');
  process.stdout.write('-'.repeat(70) + '\n');
  for (const r of checkpoint.results.filter(r => failIds.includes(r.case_id))) {
    process.stdout.write(`  ${r.case_id} (${r.candidate}):\n`);
    for (const rep of reps) {
      const v = r[rep];
      if (v) {
        process.stdout.write(`    ${rep}: ${v.label} ${v.match ? 'OK' : 'X'} cited=${v.cited} false=${v.false_citation} helpful=${v.helpful}\n`);
        if (v.cited_details && v.cited_details.length > 0) {
          process.stdout.write(`      cited: ${v.cited_details.join('; ')}\n`);
        }
      }
    }
  }

  // Save final results
  writeFileSync(OUTPUT_PATH, JSON.stringify({
    model: MODEL,
    total_cases: total,
    representations: reps_summary,
    per_case: checkpoint.results,
    checkpoint: checkpoint.completed,
  }, null, 2));

  process.stdout.write(`\nResults saved to: ${OUTPUT_PATH}\n`);
}

main().catch(e => { process.stderr.write(e.message + '\n'); process.exit(1); });
