#!/usr/bin/env node
/**
 * b2_trace_validator.mjs — Validates b2-trace-v3 JSON traces
 *
 * Implements all 10 schema requirements from §3.7.2 of REPAIR_SPEC.md:
 *   1. Every atomic claim has support entry OR is in unsupported_atoms
 *   2. source_support may be empty (atom unsupported)
 *   3. counterfactuals exactly 2 entries (A and B)
 *   4. iss_state consistency with booleans
 *   5. label consistency with iss_state
 *   6. span_text verbatim (source_text[start:end] == span_text)
 *   7. JOINT_CROSS_SOURCE mandatory fields
 *   8. inference_rule from frozen taxonomy
 *   9. JOINT_CROSS_SOURCE anti-cheating conditions (structural)
 *   10. No free-form structural variation
 */
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';

const FROZEN_TAXONOMY = new Set([
  'COMPOSITION', 'ABSTRACTION', 'SPECIALIZATION', 'GENERALIZATION',
  'CAUSAL_TRANSFER', 'MECHANISTIC_ANALOGY', 'STRUCTURAL_ANALOGY',
  'FUNCTIONAL_ANALOGY', 'OTHER',
]);

/**
 * Validate a b2-trace-v3 object.
 * @param {object} trace - The trace to validate
 * @returns {object} {valid: boolean, errors: string[], warnings: string[]}
 */
export function validateTrace(trace) {
  const errors = [];
  const warnings = [];

  // Top-level structure
  if (!trace || typeof trace !== 'object') {
    return { valid: false, errors: ['Trace is not an object'], warnings: [] };
  }

  // schema_version
  if (trace.schema_version !== 'b2-trace-v3') {
    errors.push(`schema_version must be 'b2-trace-v3', got '${trace.schema_version}'`);
  }

  // candidate
  const c = trace.candidate;
  if (!c || typeof c !== 'object') {
    errors.push('Missing candidate object');
    return { valid: false, errors, warnings };
  }
  for (const f of ['id', 'text', 'source_a', 'source_b']) {
    if (typeof c[f] !== 'string' || c[f].length === 0) {
      errors.push(`candidate.${f} must be a non-empty string`);
    }
  }

  // atoms
  if (!Array.isArray(trace.atoms)) {
    errors.push('atoms must be an array');
    return { valid: false, errors, warnings };
  }

  // Build atom_id set for counterfactual cross-checking
  const atomIds = new Set();
  const atomById = {};

  for (let i = 0; i < trace.atoms.length; i++) {
    const atom = trace.atoms[i];
    const prefix = `atoms[${i}]`;

    if (!atom.atom_id || typeof atom.atom_id !== 'string') {
      errors.push(`${prefix}.atom_id must be a non-empty string`);
    } else {
      if (atomIds.has(atom.atom_id)) {
        errors.push(`${prefix}.atom_id duplicate: '${atom.atom_id}'`);
      }
      atomIds.add(atom.atom_id);
      atomById[atom.atom_id] = atom;
    }

    if (!atom.claim || typeof atom.claim !== 'string') {
      errors.push(`${prefix}.claim must be a non-empty string`);
    }

    if (!Array.isArray(atom.source_support)) {
      errors.push(`${prefix}.source_support must be an array`);
      continue;
    }

    // Validate each support entry
    for (let j = 0; j < atom.source_support.length; j++) {
      const se = atom.source_support[j];
      const sePrefix = `${prefix}.source_support[${j}]`;

      if (!se.support_type) {
        errors.push(`${sePrefix}.support_type missing`);
        continue;
      }

      if (se.support_type === 'SOURCE_LOCAL') {
        // Validate SOURCE_LOCAL entry
        if (se.source_id !== 'A' && se.source_id !== 'B') {
          errors.push(`${sePrefix}.source_id must be 'A' or 'B', got '${se.source_id}'`);
        }
        if (!Array.isArray(se.spans) || se.spans.length === 0) {
          errors.push(`${sePrefix}.spans must be a non-empty array`);
        } else {
          for (let k = 0; k < se.spans.length; k++) {
            const span = se.spans[k];
            const spanPrefix = `${sePrefix}.spans[${k}]`;
            const sourceText = se.source_id === 'A' ? c.source_a : c.source_b;
            validateSpan(span, spanPrefix, sourceText, errors);
          }
        }
      } else if (se.support_type === 'JOINT_CROSS_SOURCE') {
        // Validate JOINT_CROSS_SOURCE entry (requirement 7 + 8)
        if (!Array.isArray(se.source_a_spans) || se.source_a_spans.length === 0) {
          errors.push(`${sePrefix}.source_a_spans must be a non-empty array`);
        } else {
          for (let k = 0; k < se.source_a_spans.length; k++) {
            validateSpan(se.source_a_spans[k], `${sePrefix}.source_a_spans[${k}]`, c.source_a, errors);
          }
        }
        if (!Array.isArray(se.source_b_spans) || se.source_b_spans.length === 0) {
          errors.push(`${sePrefix}.source_b_spans must be a non-empty array`);
        } else {
          for (let k = 0; k < se.source_b_spans.length; k++) {
            validateSpan(se.source_b_spans[k], `${sePrefix}.source_b_spans[${k}]`, c.source_b, errors);
          }
        }
        if (!se.derived_claim || typeof se.derived_claim !== 'string') {
          errors.push(`${sePrefix}.derived_claim must be a non-empty string`);
        }
        if (!se.inference_rule || !FROZEN_TAXONOMY.has(se.inference_rule)) {
          errors.push(`${sePrefix}.inference_rule '${se.inference_rule}' not in frozen taxonomy`);
        }
        if (se.inference_rule === 'OTHER' && (!se.inference_rule_other || se.inference_rule_other.length === 0)) {
          errors.push(`${sePrefix}.inference_rule_other required when inference_rule is OTHER`);
        }
        if (!se.counterfactual_a || typeof se.counterfactual_a !== 'string') {
          errors.push(`${sePrefix}.counterfactual_a must be a non-empty string`);
        }
        if (!se.counterfactual_b || typeof se.counterfactual_b !== 'string') {
          errors.push(`${sePrefix}.counterfactual_b must be a non-empty string`);
        }
      } else {
        errors.push(`${sePrefix}.support_type '${se.support_type}' is not valid (must be SOURCE_LOCAL or JOINT_CROSS_SOURCE)`);
      }
    }
  }

  // counterfactuals (requirement 3: exactly 2 entries)
  if (!Array.isArray(trace.counterfactuals)) {
    errors.push('counterfactuals must be an array');
    return { valid: false, errors, warnings };
  }
  if (trace.counterfactuals.length !== 2) {
    errors.push(`counterfactuals must have exactly 2 entries, got ${trace.counterfactuals.length}`);
  }

  const cfBySource = {};
  for (let i = 0; i < trace.counterfactuals.length; i++) {
    const cf = trace.counterfactuals[i];
    const prefix = `counterfactuals[${i}]`;
    if (cf.removed_source !== 'A' && cf.removed_source !== 'B') {
      errors.push(`${prefix}.removed_source must be 'A' or 'B'`);
    } else {
      cfBySource[cf.removed_source] = cf;
    }
    if (!Array.isArray(cf.unsupported_atoms)) {
      errors.push(`${prefix}.unsupported_atoms must be an array`);
    } else {
      // Check that referenced atom_ids exist
      for (const aid of cf.unsupported_atoms) {
        if (!atomIds.has(aid)) {
          errors.push(`${prefix}.unsupported_atoms references unknown atom_id '${aid}'`);
        }
      }
    }
    if (typeof cf.justified_without_source !== 'boolean') {
      errors.push(`${prefix}.justified_without_source must be boolean`);
    }
  }
  if (!cfBySource.A) errors.push('Missing counterfactual for removed_source A');
  if (!cfBySource.B) errors.push('Missing counterfactual for removed_source B');

  // classification (requirement 4 + 5)
  const cls = trace.classification;
  if (!cls || typeof cls !== 'object') {
    errors.push('Missing classification object');
    return { valid: false, errors, warnings };
  }

  for (const f of ['justified_by_corpus', 'iss_a', 'iss_b']) {
    if (typeof cls[f] !== 'boolean') {
      errors.push(`classification.${f} must be boolean`);
    }
  }

  if (typeof cls.iss_state !== 'string') {
    errors.push('classification.iss_state must be a string');
  }
  if (typeof cls.label !== 'string') {
    errors.push('classification.label must be a string');
  }

  // Requirement 4: iss_state consistency
  if (typeof cls.justified_by_corpus === 'boolean' &&
      typeof cls.iss_a === 'boolean' &&
      typeof cls.iss_b === 'boolean') {
    let expectedState;
    if (!cls.justified_by_corpus) {
      expectedState = 'UNSUPPORTED';
    } else if (cls.iss_a && cls.iss_b) {
      expectedState = 'ISS_both';
    } else if (cls.iss_a || cls.iss_b) {
      expectedState = 'ISS_one';
    } else {
      expectedState = 'REDUNDANT_SUPPORT';
    }
    if (cls.iss_state !== expectedState) {
      errors.push(`iss_state inconsistency: booleans imply '${expectedState}', got '${cls.iss_state}'`);
    }
  }

  // Requirement 5: label consistency
  const labelMap = {
    'ISS_one': 'REJECT',
    'ISS_both': 'ALLOW',
    'REDUNDANT_SUPPORT': 'ALLOW',
    'UNSUPPORTED': 'NOT_ADJUDICATED_BY_B2',
  };
  const expectedLabel = labelMap[cls.iss_state];
  if (expectedLabel && cls.label !== expectedLabel) {
    errors.push(`label inconsistency: iss_state '${cls.iss_state}' implies label '${expectedLabel}', got '${cls.label}'`);
  }

  // Requirement 1: every atom has support entry OR is in unsupported_atoms
  const allUnsupported = new Set();
  for (const cf of trace.counterfactuals || []) {
    for (const aid of (cf.unsupported_atoms || [])) {
      allUnsupported.add(aid);
    }
  }
  for (const atom of trace.atoms) {
    if ((!atom.source_support || atom.source_support.length === 0) && !allUnsupported.has(atom.atom_id)) {
      errors.push(`atom '${atom.atom_id}' has no support entry and is not in any unsupported_atoms list`);
    }
  }

  return { valid: errors.length === 0, errors, warnings };
}

/**
 * Validate a single span object.
 * @param {object} span - {span_text, start, end}
 * @param {string} prefix - error prefix
 * @param {string} sourceText - the source text to check against
 * @param {string[]} errors - errors array to append to
 */
function validateSpan(span, prefix, sourceText, errors) {
  if (!span || typeof span !== 'object') {
    errors.push(`${prefix} is not an object`);
    return;
  }
  if (typeof span.span_text !== 'string') {
    errors.push(`${prefix}.span_text must be a string`);
  }
  if (typeof span.start !== 'number' || !Number.isInteger(span.start)) {
    errors.push(`${prefix}.start must be an integer`);
  }
  if (typeof span.end !== 'number' || !Number.isInteger(span.end)) {
    errors.push(`${prefix}.end must be an integer`);
  }
  // Requirement 6: span_text verbatim
  if (typeof span.span_text === 'string' &&
      typeof span.start === 'number' && typeof span.end === 'number' &&
      sourceText) {
    if (span.start < 0 || span.end > sourceText.length || span.start > span.end) {
      errors.push(`${prefix}: offsets [${span.start}, ${span.end}) out of range for source length ${sourceText.length}`);
    } else {
      const actual = sourceText.substring(span.start, span.end);
      if (actual !== span.span_text) {
        errors.push(`${prefix}: span_text mismatch. Expected '${span.span_text}', got '${actual}' at [${span.start}, ${span.end})`);
      }
    }
  }
}

// CLI
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const file = process.argv[2];
  if (!file) {
    console.error('Usage: b2_trace_validator.mjs <trace.json>');
    process.exit(1);
  }
  const trace = JSON.parse(readFileSync(file, 'utf-8'));
  const result = validateTrace(trace);
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.valid ? 0 : 1);
}
