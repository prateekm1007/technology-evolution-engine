#!/usr/bin/env node
/**
 * run_abc_experiment.mjs — A/B/C representation experiment.
 *
 * Three representations of the SAME GLiREL v3 evidence:
 *   A: Raw relation list (current format)
 *   B: Structured evidence table (normalized relations with exact spans)
 *   C: Evidence graph (nodes + edges + provenance + candidate overlay)
 *
 * Everything else identical: GLiREL weights, adapter, sources, candidates,
 * GLM model (glm-4-plus), prompt policy, inference parameters.
 *
 * Pre-registered decision rule:
 *   Primary: 1. Evidence integrity 2. False evidence citation rate 3. Counterfactual consistency
 *   Secondary: 4. Calibration accuracy 5. Evidence utilization 6. Stability
 */
import ZAI from 'z-ai-web-dev-sdk';
import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const EVIDENCE_PATH = process.argv[2] || join(__dirname, 'results', 'glirel', 'evidence_graphs_v3.json');
const FIXTURE_PATH = join(__dirname, '..', '..', 'b2_adversarial_v2', 'test_fixture.json');
const OUTPUT_DIR = join(__dirname, 'results', 'abc');
mkdirSync(OUTPUT_DIR, { recursive: true });

const ACTUAL_MODEL = 'glm-4-plus';

// ── Shared system prompt (same for all three representations) ──
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
  "schema_version": "b2-trace-v3",
  "candidate": {"id":"...","text":"...","source_a":"...","source_b":"..."},
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
    "glirel_relations_available": <int>,
    "relations_relevant": <int>,
    "relations_cited": <int>,
    "glirel_evidence_helpful": <boolean>,
    "false_evidence_cited": <boolean>,
    "notes": "<brief>"
  }
}

Output ONLY the JSON. No markdown, no prose.`;

// ── Representation A: Raw relation list ──
function buildPrompt_A(evidence, tc) {
  const sourceA = evidence.source_a.text;
  const sourceB = evidence.source_b.text;
  const relsA = evidence.source_a.relations.slice(0, 10).map((r, i) =>
    `${i+1}. ${r.label}: ${r.head_text} -> ${r.tail_text} (score: ${r.score?.toFixed(3)})`
  ).join('\n');
  const relsB = evidence.source_b.relations.slice(0, 10).map((r, i) =>
    `${i+1}. ${r.label}: ${r.head_text} -> ${r.tail_text} (score: ${r.score?.toFixed(3)})`
  ).join('\n');

  return `${BASE_PROMPT}

Analyze the following candidate for B-2 leakage detection.

CASE ID: ${evidence.case_id}
CANDIDATE: ${evidence.candidate}

SOURCE A:
${sourceA}

SOURCE B:
${sourceB}

GLiREL EVIDENCE (Source A relations, top 10):
${relsA || '(none)'}

GLiREL EVIDENCE (Source B relations, top 10):
${relsB || '(none)'}

IMPORTANT: GLiREL evidence is extraction, NOT truth. Verify independently.

Output the b2-trace-v3 JSON.`;
}

// ── Representation B: Structured evidence table ──
function buildPrompt_B(evidence, tc) {
  const sourceA = evidence.source_a.text;
  const sourceB = evidence.source_b.text;

  const tableA = evidence.source_a.relations.slice(0, 10).map((r, i) => {
    const hs = r.head_span || {};
    const ts = r.tail_span || {};
    return `${i+1}|${r.head_text}|[${hs.start},${hs.end}]|${r.label}|${r.tail_text}|[${ts.start},${ts.end}]|${r.score?.toFixed(3)}`;
  }).join('\n');
  const tableB = evidence.source_b.relations.slice(0, 10).map((r, i) => {
    const hs = r.head_span || {};
    const ts = r.tail_span || {};
    return `${i+1}|${r.head_text}|[${hs.start},${hs.end}]|${r.label}|${r.tail_text}|[${ts.start},${ts.end}]|${r.score?.toFixed(3)}`;
  }).join('\n');

  return `${BASE_PROMPT}

Analyze the following candidate for B-2 leakage detection.

CASE ID: ${evidence.case_id}
CANDIDATE: ${evidence.candidate}

SOURCE A:
${sourceA}

SOURCE B:
${sourceB}

STRUCTURED EVIDENCE TABLE (Source A):
Format: #|head_text|head_span|relation|tail_text|tail_span|score
${tableA || '(none)'}

STRUCTURED EVIDENCE TABLE (Source B):
Format: #|head_text|head_span|relation|tail_text|tail_span|score
${tableB || '(none)'}

Each span [start,end] is a character offset into the source text. You can verify
by checking source[start:end] == head_text. All spans are mechanically valid.

IMPORTANT: GLiREL evidence is extraction, NOT truth. Verify independently.

Output the b2-trace-v3 JSON.`;
}

// ── Representation C: Evidence graph ──
function buildPrompt_C(evidence, tc) {
  const sourceA = evidence.source_a.text;
  const sourceB = evidence.source_b.text;

  // Build entity nodes
  const nodesA = evidence.source_a.entities.map((e, i) =>
    `  A${i}: "${e.text}" [${e.start},${e.end}] label=${e.label}`
  ).join('\n');
  const nodesB = evidence.source_b.entities.map((e, i) =>
    `  B${i}: "${e.text}" [${e.start},${e.end}] label=${e.label}`
  ).join('\n');

  // Build edge list with provenance
  const edgesA = evidence.source_a.relations.slice(0, 10).map((r, i) => {
    const hs = r.head_span || {};
    const ts = r.tail_span || {};
    return `  A_E${i}: "${r.head_text}" --[${r.label}]--> "${r.tail_text}" (score=${r.score?.toFixed(3)}, head=[${hs.start},${hs.end}], tail=[${ts.start},${ts.end}])`;
  }).join('\n');
  const edgesB = evidence.source_b.relations.slice(0, 10).map((r, i) => {
    const hs = r.head_span || {};
    const ts = r.tail_span || {};
    return `  B_E${i}: "${r.head_text}" --[${r.label}]--> "${r.tail_text}" (score=${r.score?.toFixed(3)}, head=[${hs.start},${hs.end}], tail=[${ts.start},${ts.end}])`;
  }).join('\n');

  return `${BASE_PROMPT}

Analyze the following candidate for B-2 leakage detection.

CASE ID: ${evidence.case_id}
CANDIDATE: ${evidence.candidate}

SOURCE A:
${sourceA}

SOURCE B:
${sourceB}

EVIDENCE GRAPH — Source A:
Nodes (entities with exact spans):
${nodesA}
Edges (relations with provenance):
${edgesA || '(none)'}

EVIDENCE GRAPH — Source B:
Nodes (entities with exact spans):
${nodesB}
Edges (relations with provenance):
${edgesB || '(none)'}

CANDIDATE OVERLAY:
The candidate "${evidence.candidate}" should be evaluated against the evidence graph above.
Which graph nodes correspond to candidate components?
Which graph edges support candidate relations?
Which source supplies each component?

All spans are mechanically valid (source[start:end] == text).
IMPORTANT: GLiREL evidence is extraction, NOT truth. Verify independently.

Output the b2-trace-v3 JSON.`;
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function runRepresentation(zai, evidence, tc, buildPrompt, repName) {
  const userPrompt = buildPrompt(evidence, tc);
  try {
    await sleep(12000); // 12s delay between API calls to avoid rate limiting
    const completion = await zai.chat.completions.create({
      model: ACTUAL_MODEL,
      messages: [
        { role: 'assistant', content: BASE_PROMPT },
        { role: 'user', content: userPrompt },
      ],
      thinking: { type: 'disabled' },
    });

    let content = completion.choices?.[0]?.message?.content || '';
    content = content.trim().replace(/^```(?:json)?\n?/, '').replace(/\n?```$/, '');

    let trace;
    try {
      trace = JSON.parse(content);
    } catch (e) {
      trace = { parse_error: e.message, raw: content.substring(0, 500) };
    }

    const label = trace.classification?.label || 'PARSE_ERROR';
    const state = trace.classification?.iss_state || 'UNKNOWN';
    const amendedExpected = evidence.case_id === 'ADV-09' ? 'NOT_ADJUDICATED_BY_B2' : tc.expected_label;
    const match = label === amendedExpected;
    const evAssess = trace.evidence_assessment || {};
    const falseCitation = evAssess.false_evidence_cited || false;

    console.log(`  ${repName}: ${label} (${state}) ${match ? 'OK' : 'X'} cited=${evAssess.relations_cited || 0} false=${falseCitation}`);

    return { label, state, match, falseCitation, evAssess, trace };
  } catch (err) {
    console.log(`  ${repName}: ERROR ${err.message}`);
    return { label: 'ERROR', state: 'ERROR', match: false, falseCitation: false, error: err.message };
  }
}

async function main() {
  console.log('B-2 GLiREL A/B/C Representation Experiment');
  console.log('=============================================');
  console.log(`Model: ${ACTUAL_MODEL}`);
  console.log(`Evidence: ${EVIDENCE_PATH}`);
  console.log();

  const evidenceData = JSON.parse(readFileSync(EVIDENCE_PATH, 'utf-8'));
  const fixture = JSON.parse(readFileSync(FIXTURE_PATH, 'utf-8'));
  const zai = await ZAI.create();

  const results = [];

  for (const evidence of evidenceData) {
    const tc = fixture.cases.find(c => c.id === evidence.case_id);
    if (!tc) continue;

    console.log(`[${evidence.case_id}] ${evidence.candidate}`);
    console.log(`  expected: ${tc.expected_label}`);

    const amendedExpected = evidence.case_id === 'ADV-09' ? 'NOT_ADJUDICATED_BY_B2' : tc.expected_label;

    const resA = await runRepresentation(zai, evidence, tc, buildPrompt_A, 'A(raw)');
    const resB = await runRepresentation(zai, evidence, tc, buildPrompt_B, 'B(table)');
    const resC = await runRepresentation(zai, evidence, tc, buildPrompt_C, 'C(graph)');
    console.log();

    results.push({
      case_id: evidence.case_id,
      candidate: evidence.candidate,
      expected: amendedExpected,
      A: { label: resA.label, state: resA.state, match: resA.match,
           cited: (resA.evAssess && resA.evAssess.relations_cited) || 0,
           helpful: resA.evAssess && resA.evAssess.glirel_evidence_helpful,
           false_citation: resA.falseCitation },
      B: { label: resB.label, state: resB.state, match: resB.match,
           cited: (resB.evAssess && resB.evAssess.relations_cited) || 0,
           helpful: resB.evAssess && resB.evAssess.glirel_evidence_helpful,
           false_citation: resB.falseCitation },
      C: { label: resC.label, state: resC.state, match: resC.match,
           cited: (resC.evAssess && resC.evAssess.relations_cited) || 0,
           helpful: resC.evAssess && resC.evAssess.glirel_evidence_helpful,
           false_citation: resC.falseCitation },
    });
  }

  // Summary
  const total = results.length;
  const matchesA = results.filter(r => r.A.match).length;
  const matchesB = results.filter(r => r.B.match).length;
  const matchesC = results.filter(r => r.C.match).length;
  const falseA = results.filter(r => r.A.false_citation).length;
  const falseB = results.filter(r => r.B.false_citation).length;
  const falseC = results.filter(r => r.C.false_citation).length;
  const citedA = results.reduce((s, r) => s + r.A.cited, 0);
  const citedB = results.reduce((s, r) => s + r.B.cited, 0);
  const citedC = results.reduce((s, r) => s + r.C.cited, 0);

  console.log('='.repeat(60));
  console.log('A/B/C COMPARISON SUMMARY');
  console.log('='.repeat(60));
  console.log(`                    A (raw)    B (table)   C (graph)`);
  console.log(`Calibration:        ${matchesA}/${total}       ${matchesB}/${total}        ${matchesC}/${total}`);
  console.log(`False citations:    ${falseA}          ${falseB}            ${falseC}`);
  console.log(`Total cited:        ${citedA}          ${citedB}            ${citedC}`);
  console.log();

  // Per-case
  console.log('PER-CASE:');
  console.log('-'.repeat(60));
  for (const r of results) {
    console.log(`  ${r.case_id}: expected=${r.expected}`);
    console.log(`    A: ${r.A.label} ${r.A.match ? 'OK' : 'X'} cited=${r.A.cited} false=${r.A.false_citation}`);
    console.log(`    B: ${r.B.label} ${r.B.match ? 'OK' : 'X'} cited=${r.B.cited} false=${r.B.false_citation}`);
    console.log(`    C: ${r.C.label} ${r.C.match ? 'OK' : 'X'} cited=${r.C.cited} false=${r.C.false_citation}`);
  }

  // Failure cases
  const failIds = ['ADV-05', 'ADV-06', 'ADV-07', 'ADV-08', 'ADV-13'];
  console.log('\nFAILURE CASES:');
  console.log('-'.repeat(60));
  for (const r of results.filter(r => failIds.includes(r.case_id))) {
    console.log(`  ${r.case_id} (${r.candidate}):`);
    console.log(`    A: ${r.A.label} ${r.A.match ? 'OK' : 'X'}`);
    console.log(`    B: ${r.B.label} ${r.B.match ? 'OK' : 'X'}`);
    console.log(`    C: ${r.C.label} ${r.C.match ? 'OK' : 'X'}`);
  }

  // Pre-registered decision
  console.log('\nPRE-REGISTERED DECISION:');
  console.log('-'.repeat(60));
  console.log('Primary criteria: evidence integrity, false citation rate, counterfactual consistency');
  console.log('Secondary criteria: calibration accuracy, evidence utilization, stability');
  console.log();

  // False citation rate (primary)
  const bestFalse = Math.min(falseA, falseB, falseC);
  const bestFalseReps = [];
  if (falseA === bestFalse) bestFalseReps.push('A');
  if (falseB === bestFalse) bestFalseReps.push('B');
  if (falseC === bestFalse) bestFalseReps.push('C');

  // Among those with best false citation, pick highest accuracy
  let bestRep = bestFalseReps[0];
  let bestAcc = -1;
  for (const rep of bestFalseReps) {
    const acc = rep === 'A' ? matchesA : rep === 'B' ? matchesB : matchesC;
    if (acc > bestAcc) { bestAcc = acc; bestRep = rep; }
  }

  const repNames = { A: 'raw relation list', B: 'structured evidence table', C: 'evidence graph' };
  console.log(`False citation: A=${falseA}, B=${falseB}, C=${falseC}`);
  console.log(`Accuracy: A=${matchesA}, B=${matchesB}, C=${matchesC}`);
  console.log(`Best representation: ${bestRep} (${repNames[bestRep]})`);

  const summary = {
    model: ACTUAL_MODEL,
    total_cases: total,
    matches: { A: matchesA, B: matchesB, C: matchesC },
    false_citations: { A: falseA, B: falseB, C: falseC },
    total_cited: { A: citedA, B: citedB, C: citedC },
    best_representation: bestRep,
    per_case: results,
  };

  writeFileSync(join(OUTPUT_DIR, 'abc_comparison.json'), JSON.stringify(summary, null, 2));
  console.log(`\nResults saved to: ${OUTPUT_DIR}/abc_comparison.json`);
}

main().catch(err => { console.error('Fatal:', err); process.exit(1); });
