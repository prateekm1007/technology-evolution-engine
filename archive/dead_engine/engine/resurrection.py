"""Resurrection Engine - Estimates resurrection probability (RPS)."""


class ResurrectionEngine:
    """Estimates probability that a dead technology can return."""

    def __init__(self, graph):
        self.graph = graph

    def compute_rps(self, cemetery_entry_id):
        entry = self.graph.get_node(cemetery_entry_id)
        if not entry:
            return 0.0
        conditions = entry.get('resurrection_conditions', [])
        if not conditions:
            return 0.0
        met = sum(1 for c in conditions if c.get('status') == 'met')
        approaching = sum(1 for c in conditions if c.get('status') == 'approaching')
        return (met + 0.5 * approaching) / len(conditions)