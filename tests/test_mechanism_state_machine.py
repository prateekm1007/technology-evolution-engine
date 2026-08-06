"""Tests for mechanism_state_machine.py — Mechanism extraction 6→8."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.mechanism_state_machine import (
    extract_state_transitions,
    build_mechanism_chains,
    _normalize_entity,
    _entities_match,
    MechanismChain,
    StateTransition,
)


def test_normalize_entity_strips_articles():
    """Articles 'the', 'a', 'an' are stripped."""
    assert _normalize_entity("The lithium-ion electrode") == "lithium ion electrode"
    assert _normalize_entity("the electrode") == "electrode"
    assert _normalize_entity("A sample") == "sample"
    assert _normalize_entity("An anode") == "anode"


def test_entities_match_handles_variants():
    """'The lithium-ion electrode' matches 'the electrode'."""
    assert _entities_match("The lithium-ion electrode", "the electrode")
    assert _entities_match("electrode", "The lithium-ion electrode")
    # Should NOT match unrelated entities
    assert not _entities_match("cathode", "anode")
    # Should NOT match too-short substrings
    assert not _entities_match("an", "anode")


def test_extract_single_transition():
    """A simple 'X undergoes transition from A to B' is extracted."""
    text = "The sample undergoes a phase transition from solid to liquid."
    transitions = extract_state_transitions(text)
    assert len(transitions) >= 1
    t = transitions[0]
    assert t.from_state == "solid"
    assert t.to_state == "liquid"
    assert t.transition_verb in ("undergoes", "transition")


def test_extract_reversible_transition():
    """Parenthetical (delithiation) marks the transition as reversible."""
    text = "The electrode undergoes lithiation (delithiation) during cycling."
    transitions = extract_state_transitions(text)
    assert len(transitions) >= 1
    # The reversibility flag should be True (parenthetical present)
    assert any(t.reversible for t in transitions)


def test_extract_oxidation_reduction():
    """Oxidizes/reduces pattern is recognized."""
    text = "The metal oxidizes to its oxide form."
    transitions = extract_state_transitions(text)
    assert len(transitions) >= 1


def test_build_two_step_chain():
    """Two transitions on the same entity with matching states form a 2-step chain."""
    text = (
        "The electrode undergoes a phase transition from crystalline to amorphous "
        "during charging. "
        "Subsequently, the electrode converts from amorphous to crystalline upon discharge."
    )
    transitions = extract_state_transitions(text)
    chains = build_mechanism_chains(transitions)
    # At least one chain should be ≥2 steps
    assert any(c.chain_length >= 2 for c in chains), \
        f"Expected ≥1 chain of length ≥2, got: {[(c.chain_entity, c.chain_length) for c in chains]}"


def test_chain_completeness_check():
    """A complete chain has step[N].to_state == step[N+1].from_state."""
    # Build a chain manually
    t1 = StateTransition(entity="X", from_state="A", to_state="B", transition_verb="goes")
    t2 = StateTransition(entity="X", from_state="B", to_state="C", transition_verb="goes")
    chain = MechanismChain(steps=[t1, t2], chain_entity="X", chain_length=2)
    assert chain.is_complete()

    # An incomplete chain
    t3 = StateTransition(entity="X", from_state="Z", to_state="C", transition_verb="goes")
    chain_incomplete = MechanismChain(steps=[t1, t3], chain_entity="X", chain_length=2)
    assert not chain_incomplete.is_complete()


def test_text_span_present():
    """Every extracted transition has a non-empty text_span."""
    text = "The material transforms from solid to liquid at 1500K."
    transitions = extract_state_transitions(text)
    for t in transitions:
        assert t.text_span, f"Transition {t} has empty text_span"
        assert t.text_span in text, f"text_span {t.text_span!r} not found in source"


def test_no_false_positives_on_empty_text():
    """Empty or unrelated text yields no transitions."""
    assert extract_state_transitions("") == []
    assert extract_state_transitions("This sentence has no state transitions.") == []


def test_known_state_pairs_symmetric():
    """KNOWN_STATE_PAIRS_LIST is symmetric: every (A, B) has a corresponding (B, A) entry."""
    from scripts.mechanism_state_machine import KNOWN_STATE_PAIRS_LIST, get_reverse_states
    for fwd, rev in KNOWN_STATE_PAIRS_LIST:
        # The reverse direction must be reachable via get_reverse_states
        assert fwd in get_reverse_states(rev), \
            f"Asymmetric: ({fwd}, {rev}) is in the list, but {fwd} not in get_reverse_states({rev})"
        assert rev in get_reverse_states(fwd), \
            f"Asymmetric: ({fwd}, {rev}) is in the list, but {rev} not in get_reverse_states({fwd})"


def test_multi_step_battery_cycling():
    """A realistic battery-cycling paragraph produces a multi-step chain."""
    text = (
        "During charging, the cathode undergoes lithiation (delithiation). "
        "The cathode transitions from a delithiated state to a lithiated state. "
        "Upon discharge, the cathode transitions from lithiated to delithiated."
    )
    transitions = extract_state_transitions(text)
    chains = build_mechanism_chains(transitions)
    # Should produce at least one chain of length ≥ 2
    longest = max((c.chain_length for c in chains), default=0)
    assert longest >= 2, f"Expected chain length ≥2, got max={longest}"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
