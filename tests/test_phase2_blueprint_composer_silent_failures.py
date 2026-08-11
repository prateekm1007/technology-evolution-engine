"""Tests for Phase 2 (Amendment directive): BlueprintComposer silent-failure elimination."""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from product.blueprint.composer import BlueprintComposer


# ===== Phase 2: input type validation =====

def test_non_dict_input_raises():
    bc = BlueprintComposer()
    with pytest.raises(TypeError, match="expects a dict"):
        bc.run("not a dict")
    with pytest.raises(TypeError, match="expects a dict"):
        bc.run(None)


def test_invalid_mode_raises():
    bc = BlueprintComposer()
    with pytest.raises(ValueError, match="invalid mode"):
        bc.run({'candidates': [], 'mode': 'buisness'})  # typo
    with pytest.raises(ValueError, match="invalid mode"):
        bc.run({'candidates': [], 'mode': 'invalid_mode'})


def test_non_int_max_blueprints_raises():
    bc = BlueprintComposer()
    with pytest.raises(TypeError, match="max_blueprints must be int"):
        bc.run({'candidates': [], 'max_blueprints': 'five'})
    with pytest.raises(TypeError, match="max_blueprints must be int"):
        bc.run({'candidates': [], 'max_blueprints': 5.0})


def test_negative_max_blueprints_raises():
    bc = BlueprintComposer()
    with pytest.raises(ValueError, match="max_blueprints must be >= 0"):
        bc.run({'candidates': [], 'max_blueprints': -1})


def test_non_list_candidates_raises():
    bc = BlueprintComposer()
    with pytest.raises(TypeError, match="candidates.*must be a list"):
        bc.run({'candidates': 'not a list'})


# ===== Phase 2: candidate structure validation =====

def test_non_dict_candidate_raises():
    bc = BlueprintComposer()
    with pytest.raises(TypeError, match="Candidate at index 0.*not dict"):
        bc.run({'candidates': ['not a dict']})


def test_candidate_missing_required_keys_raises():
    bc = BlueprintComposer()
    # Missing 'elements'
    with pytest.raises(KeyError, match="missing required keys"):
        bc.run({'candidates': [{'candidate_id': 'C1'}]})
    # Missing 'candidate_id'
    with pytest.raises(KeyError, match="missing required keys"):
        bc.run({'candidates': [{'elements': ['a', 'b']}]})


def test_candidate_none_candidate_id_raises():
    bc = BlueprintComposer()
    with pytest.raises(ValueError, match="invalid candidate_id"):
        bc.run({'candidates': [{'candidate_id': None, 'elements': ['a']}]})


def test_candidate_empty_string_candidate_id_raises():
    bc = BlueprintComposer()
    with pytest.raises(ValueError, match="invalid candidate_id"):
        bc.run({'candidates': [{'candidate_id': '', 'elements': ['a']}]})


def test_candidate_empty_elements_raises():
    bc = BlueprintComposer()
    with pytest.raises(ValueError, match="empty elements list"):
        bc.run({'candidates': [{'candidate_id': 'C1', 'elements': []}]})


def test_candidate_non_list_elements_raises():
    bc = BlueprintComposer()
    with pytest.raises(TypeError, match="'elements' must be list"):
        bc.run({'candidates': [{'candidate_id': 'C1', 'elements': 'not a list'}]})


def test_candidate_non_numeric_composite_score_raises():
    bc = BlueprintComposer()
    with pytest.raises(TypeError, match="composite_score must be numeric"):
        bc.run({'candidates': [
            {'candidate_id': 'C1', 'elements': ['a', 'b'], 'composite_score': 'high'}
        ]})


# ===== Phase 2: DR-63 derived scores are flagged =====

def test_dr63_derived_score_is_flagged():
    """When composite_score is missing and DR-63 derives one, the candidate
    must be flagged with _dr63_score_derived=True so downstream consumers
    can distinguish real scores from derived defaults."""
    bc = BlueprintComposer()
    # Candidate with no composite_score — DR-63 will derive one
    result = bc.run({
        'candidates': [
            {'candidate_id': 'C1', 'elements': ['a', 'b', 'c', 'd', 'e'], 'adjacent_domains': ['d1', 'd2']}
        ],
        'mode': 'business',
    })
    assert result['n_dr63_derived_scores'] == 1
    # The blueprint itself should carry the flag
    if result['blueprints']:
        assert result['blueprints'][0]['dr63_score_derived'] is True


def test_real_score_not_flagged_as_derived():
    """When composite_score is provided, _dr63_score_derived should be False."""
    bc = BlueprintComposer()
    result = bc.run({
        'candidates': [
            {'candidate_id': 'C1', 'elements': ['a', 'b'], 'composite_score': 0.7}
        ],
        'mode': 'business',
    })
    assert result['n_dr63_derived_scores'] == 0


# ===== Phase 2: blueprint generation errors are surfaced =====

def test_blueprint_generation_errors_are_surfaced():
    """If a single candidate causes _bp() to fail, the error should be
    recorded in 'blueprint_generation_errors' rather than crashing the
    whole batch."""
    bc = BlueprintComposer()
    # Create a candidate that passes validation but has a weird structure
    # that might cause issues downstream. We'll monkey-patch _bp to fail.
    original_bp = bc._bp
    call_count = [0]

    def failing_bp(c, mode):
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError("simulated _bp failure")
        return original_bp(c, mode)

    bc._bp = failing_bp
    result = bc.run({
        'candidates': [
            {'candidate_id': 'C1', 'elements': ['a', 'b'], 'composite_score': 0.7},
            {'candidate_id': 'C2', 'elements': ['c', 'd'], 'composite_score': 0.6},
        ],
        'mode': 'business',
    })
    assert len(result['blueprint_generation_errors']) >= 1
    assert 'C1' in str(result['blueprint_generation_errors'])


# ===== Phase 2: regression — valid input still works =====

def test_valid_business_input_still_produces_blueprints():
    bc = BlueprintComposer()
    result = bc.run({
        'candidates': [
            {'candidate_id': 'C1', 'elements': ['graphene', 'supercapacitor'], 'composite_score': 0.7}
        ],
        'mode': 'business',
        'max_blueprints': 5,
    })
    assert len(result['blueprints']) == 1
    assert result['mode'] == 'business'
    assert result['total_viable'] == 1


def test_valid_consumer_input_still_produces_blueprints():
    bc = BlueprintComposer()
    result = bc.run({
        'candidates': [
            {'candidate_id': 'C1', 'elements': ['sensor', 'membrane'], 'composite_score': 0.5}
        ],
        'mode': 'consumer',
        'max_blueprints': 3,
    })
    assert len(result['blueprints']) == 1
    assert result['mode'] == 'consumer'


def test_low_score_candidates_filtered_out():
    """Candidates with composite_score <= 0.3 should not produce blueprints."""
    bc = BlueprintComposer()
    result = bc.run({
        'candidates': [
            {'candidate_id': 'C1', 'elements': ['a'], 'composite_score': 0.2},  # below threshold
            {'candidate_id': 'C2', 'elements': ['b', 'c'], 'composite_score': 0.6},  # above
        ],
        'mode': 'business',
    })
    assert len(result['blueprints']) == 1
    assert result['blueprints'][0]['candidate_id'] == 'C2'


def test_max_blueprints_truncates():
    bc = BlueprintComposer()
    result = bc.run({
        'candidates': [
            {'candidate_id': f'C{i}', 'elements': ['a', 'b'], 'composite_score': 0.5 + i * 0.01}
            for i in range(10)
        ],
        'mode': 'business',
        'max_blueprints': 3,
    })
    assert len(result['blueprints']) == 3


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
