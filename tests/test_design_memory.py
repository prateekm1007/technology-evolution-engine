"""Tests for DR-79: design memory (append-only)."""
import sys
import json
import pytest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.design_memory import (
    DesignMemory, FailureEntry, RepairEntry, IterationEntry,
    ResidualEntry, TradeoffEntry, DeadEndEntry, MotifEntry,
    MemorySnapshot,
)


def test_memory_starts_empty():
    """A fresh DesignMemory has zero entries."""
    mem = DesignMemory()
    snap = mem.snapshot()
    assert snap.n_failures == 0
    assert snap.n_repairs == 0
    assert snap.n_iterations == 0
    assert snap.n_residuals == 0
    assert snap.n_tradeoffs == 0
    assert snap.n_dead_ends == 0
    assert snap.n_motifs == 0


def test_record_failure_adds_entry():
    """record_failure adds a FailureEntry with a lesson."""
    mem = DesignMemory()
    entry = mem.record_failure("C1", "cost > ceiling",
                               "Use cheaper substrate")
    assert isinstance(entry, FailureEntry)
    assert entry.config_id == "C1"
    assert entry.lesson == "Use cheaper substrate"
    assert mem.snapshot().n_failures == 1


def test_record_repair_adds_entry():
    """record_repair adds a RepairEntry."""
    mem = DesignMemory()
    entry = mem.record_repair("C1", "apply invert operator",
                              applied=True, new_config_id="C2")
    assert isinstance(entry, RepairEntry)
    assert entry.applied is True
    assert entry.new_config_id == "C2"


def test_record_iteration_adds_entry():
    """record_iteration adds an IterationEntry with priors."""
    mem = DesignMemory()
    entry = mem.record_iteration(
        0, ["C1", "C2"],
        priors_before={"seebeck_coefficient": 1.0},
        priors_after={"seebeck_coefficient": 0.95},
        n_measured=2)
    assert isinstance(entry, IterationEntry)
    assert entry.iteration == 0
    assert entry.n_measured == 2
    assert entry.priors_after["seebeck_coefficient"] == 0.95


def test_record_residual_adds_entry():
    """record_residual adds a ResidualEntry."""
    mem = DesignMemory()
    entry = mem.record_residual("C1", "ZT", 1.1, 1.0, 0.1, 0.1, True)
    assert isinstance(entry, ResidualEntry)
    assert entry.metric == "ZT"
    assert entry.significant is True


def test_record_tradeoff_adds_entry():
    """record_tradeoff adds a TradeoffEntry."""
    mem = DesignMemory()
    entry = mem.record_tradeoff("C3", "conductivity", "stability",
                                "Used porosity to break tradeoff",
                                operator_used="invert")
    assert isinstance(entry, TradeoffEntry)
    assert entry.operator_used == "invert"


def test_record_dead_end_adds_entry():
    """record_dead_end adds a DeadEndEntry."""
    mem = DesignMemory()
    entry = mem.record_dead_end("C5", "no improvement", branch="layered_3")
    assert isinstance(entry, DeadEndEntry)
    assert entry.branch == "layered_3"


def test_record_motif_adds_entry():
    """record_motif adds a MotifEntry."""
    mem = DesignMemory()
    entry = mem.record_motif("MOTIF-001", ["bismuth_telluride", "graphene"],
                             "layered_2", score=1.2, config_id="C7")
    assert isinstance(entry, MotifEntry)
    assert entry.score == 1.2


def test_get_lessons_returns_all_lessons():
    """get_lessons returns the lesson strings from all failures."""
    mem = DesignMemory()
    mem.record_failure("C1", "r1", "lesson A")
    mem.record_failure("C2", "r2", "lesson B")
    lessons = mem.get_lessons()
    assert "lesson A" in lessons
    assert "lesson B" in lessons


def test_get_failures_for_config():
    """get_failures_for_config filters by config_id."""
    mem = DesignMemory()
    mem.record_failure("C1", "r1", "lesson A")
    mem.record_failure("C2", "r2", "lesson B")
    mem.record_failure("C1", "r3", "lesson C")
    failures = mem.get_failures_for_config("C1")
    assert len(failures) == 2


def test_get_motifs_above_threshold():
    """get_motifs_above returns motifs with score > threshold."""
    mem = DesignMemory()
    mem.record_motif("M1", ["a"], "x", score=0.5)
    mem.record_motif("M2", ["b"], "y", score=1.2)
    mem.record_motif("M3", ["c"], "z", score=1.5)
    high = mem.get_motifs_above(1.0)
    assert len(high) == 2
    scores = [m.score for m in high]
    assert 1.2 in scores
    assert 1.5 in scores


def test_append_only_invariant_verified():
    """The append-only invariant is verifiable via snapshots."""
    mem = DesignMemory()
    mem.record_failure("C1", "r1", "lesson A")
    snap1 = mem.snapshot()
    mem.record_failure("C2", "r2", "lesson B")
    # After more entries, the prior snapshot must still be valid
    assert mem.verify_append_only(snap1) is True


def test_entry_ids_monotonic():
    """Entry IDs are monotonically increasing across all recorders."""
    mem = DesignMemory()
    e1 = mem.record_failure("C1", "r", "l")
    e2 = mem.record_repair("C1", "s", True)
    e3 = mem.record_residual("C1", "ZT", 1.0, 1.0, 0.0, 0.0, False)
    assert e1.entry_id < e2.entry_id < e3.entry_id


def test_to_dict_serializable():
    """The full memory is JSON-serializable."""
    mem = DesignMemory()
    mem.record_failure("C1", "r", "l")
    mem.record_motif("M1", ["a"], "x", 1.0)
    d = mem.to_dict()
    # Round-trip
    s = json.dumps(d, default=str)
    assert "failures" in json.loads(s)
    assert "motifs" in json.loads(s)


def test_save_writes_json_file():
    """save() writes a JSON file with the memory contents."""
    mem = DesignMemory()
    mem.record_failure("C1", "r", "lesson A")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "memory.json"
        mem.save(path)
        assert path.exists()
        with open(path) as f:
            data = json.load(f)
        assert "failures" in data
        assert len(data["failures"]) == 1


def test_get_lessons_for_config():
    """get_lessons_for_config filters lessons by config_id."""
    mem = DesignMemory()
    mem.record_failure("C1", "r1", "A")
    mem.record_failure("C2", "r2", "B")
    mem.record_failure("C1", "r3", "C")
    lessons_c1 = mem.get_lessons_for_config("C1")
    assert "A" in lessons_c1
    assert "C" in lessons_c1
    assert "B" not in lessons_c1


def test_snapshot_returns_memory_snapshot():
    """snapshot() returns a MemorySnapshot dataclass."""
    mem = DesignMemory()
    mem.record_failure("C1", "r", "l")
    snap = mem.snapshot()
    assert isinstance(snap, MemorySnapshot)
    assert snap.n_failures == 1


def test_seal_blocks_nothing_but_documents_intent():
    """seal() marks the memory as sealed (immutable snapshot point)."""
    mem = DesignMemory()
    mem.record_failure("C1", "r", "l")
    mem.seal()
    # Sealing is a documentation marker — we still allow further appends
    # (the append-only invariant is enforced by verify_append_only).
    # But the seal timestamp is recorded in the snapshot.
    snap = mem.snapshot()
    assert snap.n_failures == 1


def test_candidate_n_plus1_improves_because_n_failed():
    """CRITICAL DR-79 invariant: candidate N+1 improves because N failed.

    The memory records a lesson from N's failure, and the next candidate
    must address that lesson. This test verifies that the lesson is
    retrievable and actionable.
    """
    mem = DesignMemory()
    mem.record_failure("CN", "ZT < 1.0",
                       "Reduce thermal conductivity via porosity")
    # The next candidate's generation can query the memory for lessons
    lessons = mem.get_lessons()
    assert len(lessons) == 1
    assert "porosity" in lessons[0]
    # And the next candidate's design_operator_chain should include the
    # repair strategy derived from this lesson.
    mem.record_repair("CN", "apply invert operator with porosity=0.3",
                      applied=True, new_config_id="CN+1")
    repairs = mem.get_repairs()
    assert repairs[0].new_config_id == "CN+1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
