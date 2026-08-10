#!/usr/bin/env node
import ZAI from 'z-ai-web-dev-sdk';
import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const evidence = JSON.parse(readFileSync(join(__dirname, 'results/glirel/evidence_graphs_v3.json'), 'utf-8'));
  const fixture = JSON.parse(readFileSync(join(__dirname, '..', '..', 'b2_adversarial_v2', 'test_fixture.json'), 'utf-8'));
  const zai = await ZAI.create();
  const MODEL = 'glm-4-plus';
  mkdirSync(join(__dirname, 'results', 'abc'), { recursive: true });

  const BASE = 'You are a B-2 leakage detector. Determine: ISS_one->REJECT, ISS_both->ALLOW, REDUNDANT_SUPPORT->ALLOW, UNSUPPORTED->NOT_ADJUDICATED_BY_B2. GLiREL evidence is extraction NOT truth. Verify independently. Output ONLY JSON with: {classification:{justified_by_corpus,iss_a,iss_b,iss_state,label}, evidence_assessment:{relations_cited,glirel_evidence_helpful,false_evidence_cited}}';

  const results = [];

  for (const ev of evidence) {
    const tc = fixture.cases.find(c => c.id === ev.case_id);
    if (!tc) continue;
    const amended = ev.case_id === 'ADV-09' ? 'NOT_ADJUDICATED_BY_B2' : tc.expected_label;
    const row = { case_id: ev.case_id, candidate: ev.candidate, expected: amended };

    const prompts = {
      A: 'CASE: ' + ev.case_id + '\nCANDIDATE: ' + ev.candidate + '\nSOURCE A:\n' + ev.source_a.text + '\nSOURCE B:\n' + ev.source_b.text + '\nGLiREL A:\n' + ev.source_a.relations.slice(0, 10).map((r, i) => (i + 1) + '. ' + r.label + ': ' + r.head_text + ' -> ' + r.tail_text).join('\n') + '\nGLiREL B:\n' + ev.source_b.relations.slice(0, 10).map((r, i) => (i + 1) + '. ' + r.label + ': ' + r.head_text + ' -> ' + r.tail_text).join('\n') + '\nOutput JSON.',
      B: 'CASE: ' + ev.case_id + '\nCANDIDATE: ' + ev.candidate + '\nSOURCE A:\n' + ev.source_a.text + '\nSOURCE B:\n' + ev.source_b.text + '\nTABLE A (head|span|rel|tail|span|score):\n' + ev.source_a.relations.slice(0, 10).map((r, i) => (i + 1) + '|' + r.head_text + '|[' + r.head_span.start + ',' + r.head_span.end + ']|' + r.label + '|' + r.tail_text + '|[' + r.tail_span.start + ',' + r.tail_span.end + ']|' + r.score.toFixed(3)).join('\n') + '\nTABLE B:\n' + ev.source_b.relations.slice(0, 10).map((r, i) => (i + 1) + '|' + r.head_text + '|[' + r.head_span.start + ',' + r.head_span.end + ']|' + r.label + '|' + r.tail_text + '|[' + r.tail_span.start + ',' + r.tail_span.end + ']|' + r.score.toFixed(3)).join('\n') + '\nAll spans valid. Verify source[start:end]==text. Output JSON.',
      C: 'CASE: ' + ev.case_id + '\nCANDIDATE: ' + ev.candidate + '\nSOURCE A:\n' + ev.source_a.text + '\nSOURCE B:\n' + ev.source_b.text + '\nGRAPH A Nodes:\n' + ev.source_a.entities.map((en, i) => '  A' + i + ': "' + en.text + '" [' + en.start + ',' + en.end + '] ' + en.label).join('\n') + '\nGRAPH A Edges:\n' + ev.source_a.relations.slice(0, 10).map((r, i) => '  A_E' + i + ': "' + r.head_text + '" --[' + r.label + ']--> "' + r.tail_text + '" (score=' + r.score.toFixed(3) + ')').join('\n') + '\nGRAPH B Nodes:\n' + ev.source_b.entities.map((en, i) => '  B' + i + ': "' + en.text + '" [' + en.start + ',' + en.end + '] ' + en.label).join('\n') + '\nGRAPH B Edges:\n' + ev.source_b.relations.slice(0, 10).map((r, i) => '  B_E' + i + ': "' + r.head_text + '" --[' + r.label + ']--> "' + r.tail_text + '" (score=' + r.score.toFixed(3) + ')').join('\n') + '\nCANDIDATE OVERLAY: "' + ev.candidate + '" — which nodes/edges support it?\nAll spans valid. Verify independently. Output JSON.',
    };

    for (const rep of ['A', 'B', 'C']) {
      await sleep(15000);
      try {
        const c = await zai.chat.completions.create({
          model: MODEL,
          messages: [{ role: 'assistant', content: BASE }, { role: 'user', content: prompts[rep] }],
          thinking: { type: 'disabled' },
        });
        let content = (c.choices?.[0]?.message?.content || '').trim().replace(/^```(?:json)?\n?/, '').replace(/\n?```$/, '');
        let trace;
        try { trace = JSON.parse(content); } catch (e) { trace = { classification: { label: 'PARSE_ERROR' }, evidence_assessment: {} }; }
        const label = trace.classification?.label || 'ERROR';
        const state = trace.classification?.iss_state || 'UNKNOWN';
        const match = label === amended;
        const cited = trace.evidence_assessment?.relations_cited || 0;
        const falseCit = trace.evidence_assessment?.false_evidence_cited || false;
        row[rep] = { label, state, match, cited, false_citation: falseCit };
        console.log('[' + ev.case_id + '] ' + rep + ': ' + label + ' ' + (match ? 'OK' : 'X') + ' cited=' + cited, true);
      } catch (err) {
        row[rep] = { label: 'ERROR', state: 'ERROR', match: false, cited: 0, false_citation: false };
        console.log('[' + ev.case_id + '] ' + rep + ': ERROR ' + err.message, true);
      }
    }
    results.push(row);
  }

  const matches = { A: results.filter(r => r.A?.match).length, B: results.filter(r => r.B?.match).length, C: results.filter(r => r.C?.match).length };
  const falseCit = { A: results.filter(r => r.A?.false_citation).length, B: results.filter(r => r.B?.false_citation).length, C: results.filter(r => r.C?.false_citation).length };
  console.log('\n=== SUMMARY ===', true);
  console.log('Matches: A=' + matches.A + ' B=' + matches.B + ' C=' + matches.C, true);
  console.log('False citations: A=' + falseCit.A + ' B=' + falseCit.B + ' C=' + falseCit.C, true);
  writeFileSync(join(__dirname, 'results', 'abc', 'abc_comparison.json'), JSON.stringify({ results, matches, false_citations: falseCit }, null, 2));
}

main().catch(e => console.error(e));
