import hashlib
from product.scoring.epistemic_status import migrate_confidence_to_typed


# Phase 2: valid modes are explicit. The old code silently treated any
# non-'consumer' mode as 'business', which made typos like 'buisness'
# produce a business report silently. Now invalid modes raise.
_VALID_MODES = {'business', 'consumer'}

# Phase 2: required candidate keys. A candidate missing any of these
# is structurally invalid and must NOT be silently filled in.
# (DR-63 added a partial fix that filled in composite_score — that
# fix is preserved for backward compatibility, but the candidate is
# now flagged with `_dr63_score_derived: true` so downstream consumers
# can distinguish real scores from derived defaults.)
_REQUIRED_CANDIDATE_KEYS = {'candidate_id', 'elements'}


class BlueprintComposer:
    """Blueprint composer.

    Phase 2 (Amendment directive) — Silent failure elimination:

    The old code silently filled in missing candidate fields (composite_score,
    elements, candidate_id, operator_applied) with derived defaults.
    That made a malformed candidate look like a valid one — exactly the
    silent-failure pattern the Amendment directive targets.

    The fix:
      - reject non-dict input
      - reject invalid mode (no silent 'business' default)
      - reject non-int / negative max_blueprints
      - flag DR-63 derived scores with `_dr63_score_derived: true`
      - reject candidates missing required keys (candidate_id, elements)
      - reject candidates with empty elements list (would produce an
        empty blueprint that looks valid)
      - reject candidates with None/non-string candidate_id (would crash
        in _bp() with unhelpful AttributeError)

    Per the Final Non-Negotiable Principle, a blueprint produced from
    a malformed candidate is a circular measurement — it looks like a
    result but is actually an artifact of the composer's fill-in logic.
    """

    def run(self, d):
        # Phase 2: input type check
        if not isinstance(d, dict):
            raise TypeError(
                f"BlueprintComposer.run() expects a dict, got {type(d).__name__}. "
                f"A non-dict input is a silent-failure signature (Phase 2 fix)."
            )

        cs = d.get('candidates', [])
        mode = d.get('mode', 'business')
        mx = d.get('max_blueprints', 5)

        # Phase 2: validate mode explicitly
        if mode not in _VALID_MODES:
            raise ValueError(
                f"BlueprintComposer.run() received invalid mode "
                f"{repr(mode)}. Valid modes: {sorted(_VALID_MODES)}. "
                f"The old code silently treated any non-'consumer' mode "
                f"as 'business', masking caller typos (Phase 2 fix)."
            )

        # Phase 2: validate max_blueprints
        if not isinstance(mx, int) or isinstance(mx, bool):
            raise TypeError(
                f"BlueprintComposer.run() max_blueprints must be int, "
                f"got {type(mx).__name__}={repr(mx)}. "
                f"A non-int max_blueprints silently produces wrong slice "
                f"behavior (Phase 2 fix)."
            )
        if mx < 0:
            raise ValueError(
                f"BlueprintComposer.run() max_blueprints must be >= 0, "
                f"got {mx}. A negative value silently produces an empty "
                f"blueprint list (Phase 2 fix)."
            )

        # Phase 2: validate candidates is a list
        if not isinstance(cs, list):
            raise TypeError(
                f"BlueprintComposer.run() 'candidates' must be a list, "
                f"got {type(cs).__name__}. A non-list candidates value "
                f"would silently produce 0 blueprints (Phase 2 fix)."
            )

        # Phase 2: validate each candidate's structure
        validated_candidates = []
        for i, c in enumerate(cs):
            if not isinstance(c, dict):
                raise TypeError(
                    f"Candidate at index {i} is {type(c).__name__}, not dict. "
                    f"A non-dict candidate is a silent-failure signature "
                    f"(Phase 2 fix)."
                )
            missing = [k for k in _REQUIRED_CANDIDATE_KEYS if k not in c]
            if missing:
                raise KeyError(
                    f"Candidate at index {i} missing required keys: {missing}. "
                    f"The old code silently filled these in with derived "
                    f"defaults, making a malformed candidate look valid "
                    f"(Phase 2 fix)."
                )

            # Phase 2: candidate_id must be a non-empty string
            cid = c.get('candidate_id')
            if not isinstance(cid, str) or not cid.strip():
                raise ValueError(
                    f"Candidate at index {i} has invalid candidate_id "
                    f"{repr(cid)}. Must be non-empty string. The old code's "
                    f"setdefault would produce 'CAND-XXXXXX' but only if the "
                    f"key was missing — a None value would crash later in "
                    f"_bp() with an unhelpful AttributeError (Phase 2 fix)."
                )

            # Phase 2: elements must be a non-empty list
            el = c.get('elements')
            if not isinstance(el, list):
                raise TypeError(
                    f"Candidate {cid} 'elements' must be list, "
                    f"got {type(el).__name__}."
                )
            if len(el) == 0:
                raise ValueError(
                    f"Candidate {cid} has empty elements list. An empty "
                    f"elements list would produce a blueprint with empty "
                    f"title, empty subsystems, and cost_estimate_usd=0 — "
                    f"a malformed blueprint that looks valid (Phase 2 fix)."
                )

            # DR-63 backward-compat: derive composite_score if missing,
            # but flag it so downstream consumers know it was derived.
            if 'composite_score' not in c:
                n_elements = len(el)
                n_domains = len(c.get('adjacent_domains', [])) + 1
                c['composite_score'] = min(0.8, 0.2 * n_elements + 0.1 * n_domains)
                c['_dr63_score_derived'] = True  # NEW: provenance flag
            else:
                c.setdefault('_dr63_score_derived', False)

            # Phase 2: validate composite_score is numeric (if present)
            cs_score = c.get('composite_score')
            if not isinstance(cs_score, (int, float)) or isinstance(cs_score, bool):
                raise TypeError(
                    f"Candidate {cid} composite_score must be numeric, "
                    f"got {type(cs_score).__name__}={repr(cs_score)}. "
                    f"A non-numeric score silently breaks downstream "
                    f"sorting and filtering (Phase 2 fix)."
                )

            # DR-63 backward-compat: fill in operator_applied if missing
            c.setdefault('operator_applied', 'none')

            validated_candidates.append(c)

        # Filter and sort
        viable = sorted(
            [c for c in validated_candidates if c.get('composite_score', 0) > 0.3],
            key=lambda c: c.get('composite_score', 0),
            reverse=True
        )[:mx]

        # Phase 2: wrap each _bp() call so a single malformed candidate
        # doesn't crash the whole batch. Record the error in the result.
        blueprints = []
        bp_errors = []  # NEW
        for c in viable:
            try:
                blueprints.append(self._bp(c, mode))
            except Exception as e:
                bp_errors.append({
                    'candidate_id': c.get('candidate_id', '?'),
                    'error': f"{type(e).__name__}: {e}",
                })

        return {
            'blueprints': blueprints,
            'total_viable': len(viable),
            'mode': mode,
            'blueprint_generation_errors': bp_errors,  # NEW: surface errors
            'n_dr63_derived_scores': sum(1 for c in validated_candidates if c.get('_dr63_score_derived')),
        }

    def _bp(self, c, mode):
        el = c.get('elements', [])
        op = c.get('operator_applied', 'none')
        cid = c.get('candidate_id', '?')
        # Phase 2: cid is now validated as non-empty string in run().
        # This encode() call cannot fail.
        bpid = 'BP-' + hashlib.sha256(cid.encode()).hexdigest()[:10].upper()
        opn = op.replace('_', ' ').title() if op != 'none' else 'Combination'
        title = opn + ': ' + ' + '.join(str(e)[:30] for e in el[:3])

        legacy_conf = c.get('composite_score', 0.0)
        typed = migrate_confidence_to_typed(legacy_conf)

        bp = {
            'blueprint_id': bpid,
            'candidate_id': cid,
            'title': title,
            'summary': self._sum(el, op, c),
            'build_concept': self._concept(el, op),
            'subsystem_architecture': self._subs(el),
            'bom': self._bom(el, mode),
            'prototype_plan': self._plan(el, mode),
            'risks': self._risks(c),
            'patent_differentiation': self._diff(el, op) if mode == 'business' else [],
            'next_experiments': self._exps(el, c),
            'cost_estimate_usd': len(el) * 500.0 * (10.0 if mode == 'business' else 1.0),
            'timeline_estimate_days': (30 + len(el) * 10) * (3 if mode == 'business' else 1),
            'skill_required': self._skill(el, op),
            'assumptions': c.get('assumptions', []),
            'epistemic_status': typed['epistemic_status'],
            'legacy_confidence_deprecated': typed['legacy_confidence_deprecated'],
            'mode': mode,
            'dr63_score_derived': c.get('_dr63_score_derived', False),  # NEW
        }
        if mode == 'consumer':
            bp['subsystem_architecture'] = bp['subsystem_architecture'][:3]
            bp['bom'] = bp['bom'][:5]
            bp['prototype_plan'] = bp['prototype_plan'][:3]
        return bp

    def _sum(self, el, op, c):
        s = 'A ' + str(len(el)) + '-element combination'
        if op != 'none':
            s += ' with ' + op.replace('_', ' ') + ' applied'
        # Phase 2: pcs and cis may be missing (DR-63 derived candidates).
        # Use a safe default of 0.0 and round.
        pcs = c.get('pcs', 0.0)
        cis = c.get('cis', 0.0)
        # Phase 2: validate they're numeric; if not, record as 0.0
        if not isinstance(pcs, (int, float)) or isinstance(pcs, bool):
            pcs = 0.0
        if not isinstance(cis, (int, float)) or isinstance(cis, bool):
            cis = 0.0
        s += '. PCS=' + str(round(pcs, 2)) + ', CIS=' + str(round(cis, 2)) + '.'
        if c.get('cemetery_risk', 0) > 0:
            s += ' Overlaps with known historical failures.'
        return s

    def _concept(self, el, op):
        ps = ['Subsystem ' + str(i + 1) + ': Integrate ' + str(e) for i, e in enumerate(el)]
        om = {
            'eliminate': 'Remove non-essential subsystems.',
            'substitute': 'Replace constrained materials.',
            'miniaturize': 'Scale down dimensions.',
            'distribute': 'Distribute across nodes.',
            'modularize': 'Decompose into modules.',
            'software_substitution': 'Replace hardware with software.',
            'change_energy_domain': 'Shift energy domain.',
            'change_information_domain': 'Shift information domain.',
        }
        if op in om:
            ps.append(om[op])
        return chr(10).join(ps)

    def _subs(self, el):
        return [
            {
                'name': 'Subsystem-' + str(i + 1),
                'core_element': str(e),
                'function': 'Provides ' + str(e) + ' capability',
                'interfaces': [
                    'Connects to Subsystem-' + str(j + 1)
                    for j in range(len(el)) if j != i
                ],
            }
            for i, e in enumerate(el)
        ]

    def _bom(self, el, mode):
        bom = [
            {
                'item': str(e), 'category': 'core_component',
                'quantity': 1, 'notes': 'Verify availability',
            }
            for e in el
        ]
        if mode == 'business':
            bom += [
                {'item': 'Integration hardware', 'category': 'infrastructure', 'quantity': 1, 'notes': 'Architecture-dependent'},
                {'item': 'Testing equipment', 'category': 'validation', 'quantity': 1, 'notes': 'Domain-specific'},
            ]
        return bom

    def _plan(self, el, mode):
        p = [
            {'phase': 1, 'name': 'Proof of Concept', 'duration_days': 14, 'goal': 'Validate core interactions'},
            {'phase': 2, 'name': 'Breadboard', 'duration_days': 21, 'goal': 'Low-fidelity integration'},
            {'phase': 3, 'name': 'Functional Prototype', 'duration_days': 30, 'goal': 'Working prototype'},
        ]
        if mode == 'business':
            p += [
                {'phase': 4, 'name': 'DFM', 'duration_days': 45, 'goal': 'Optimize for production'},
                {'phase': 5, 'name': 'Pilot', 'duration_days': 60, 'goal': 'Small batch'},
            ]
        return p

    def _risks(self, c):
        r = []
        if c.get('cemetery_risk', 0) > 0:
            r.append({'risk': 'Historical failure overlap', 'severity': 'high', 'mitigation': 'Review cemetery entries'})
        if c.get('pcs', 1) < 0.5:
            r.append({'risk': 'Missing prerequisites', 'severity': 'high', 'mitigation': 'Develop prerequisites first'})
        if c.get('feasibility', 1) < 0.4:
            r.append({'risk': 'Low feasibility', 'severity': 'medium', 'mitigation': 'Try alternative operators'})
        r.append({'risk': 'Integration complexity', 'severity': 'medium', 'mitigation': 'Modular interfaces'})
        return r

    def _diff(self, el, op):
        d = []
        if op != 'none':
            d.append({'claim': 'Novel ' + op.replace('_', ' ') + ' application', 'strength': 'medium'})
        if len(el) >= 3:
            d.append({'claim': 'Novel ' + str(len(el)) + '-element combination', 'strength': 'medium'})
        d.append({'claim': 'Specific integration architecture', 'strength': 'high'})
        return d

    def _exps(self, el, c):
        e = [
            {'experiment': 'Element compatibility test', 'hypothesis': 'Core elements interface without degradation', 'priority': 1},
            {'experiment': 'Operator effect validation', 'hypothesis': 'Operator improves target metric', 'priority': 2},
        ]
        if c.get('cemetery_risk', 0) > 0:
            e.insert(0, {'experiment': 'Historical failure replication', 'hypothesis': 'Failure mode mitigated', 'priority': 0})
        return e

    def _skill(self, el, op):
        cx = len(el) + (2 if op in ('change_energy_domain', 'change_information_domain') else 0)
        if cx <= 2:
            return 'beginner'
        if cx <= 4:
            return 'intermediate'
        if cx <= 6:
            return 'advanced'
        return 'expert'
