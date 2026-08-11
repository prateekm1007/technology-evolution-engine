"""Tests for Phase 2-4 work (cycle 198): DR-62, DR-63, DR-68."""
import sys
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# DR-62: BusinessPipeline input validation

def test_dr62_wrong_key_raises():
    """DR-62: {'text': ...} raises ValueError, not silent empty result."""
    from product.business.pipeline import BusinessPipeline
    bp = BusinessPipeline()
    with pytest.raises(ValueError, match="raw_text"):
        bp.run({'text': 'graphene'})


def test_dr62_correct_key_works():
    """DR-62: {'raw_text': ...} produces blueprints."""
    from product.business.pipeline import BusinessPipeline
    bp = BusinessPipeline()
    result = bp.run({'raw_text': 'graphene supercapacitor'})
    assert len(result['blueprints']) > 0


# DR-63: Blueprint composer handles pipeline candidates

def test_dr63_composer_handles_pipeline_candidates():
    """DR-63: composer produces blueprints from extraction pipeline candidates."""
    from product.blueprint.composer import BlueprintComposer
    bc = BlueprintComposer()
    result = bc.run({
        'candidates': [
            {'domain': 'energy', 'adjacent_domains': ['materials'],
             'permutation': {'material': 'graphene', 'application': 'supercapacitor'}},
        ],
        'mode': 'business',
        'max_blueprints': 5,
    })
    assert len(result['blueprints']) > 0
    bp = result['blueprints'][0]
    assert 'bom' in bp
    assert 'cost_estimate_usd' in bp
    assert 'epistemic_status' in bp


# DR-68: Auto re-audit scheduler

def test_dr68_scheduler_importable():
    """DR-68: auto_reaudit_scheduler is importable."""
    from scripts.auto_reaudit_scheduler import should_run_reaudit, get_current_cycle
    assert should_run_reaudit is not None
    assert get_current_cycle() > 0


def test_dr68_scheduler_logs_to_ledger():
    """DR-68: running the scheduler logs an auto_reaudit entry to the ledger."""
    import json
    ledger = Path(__file__).resolve().parents[1] / "data" / "ledger" / "predictions.jsonl"
    # Check that at least one auto_reaudit entry exists
    found = False
    with ledger.open() as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("type") == "auto_reaudit":
                    found = True
                    break
            except json.JSONDecodeError:
                continue
    assert found, "auto_reaudit entry must exist in predictions.jsonl"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
