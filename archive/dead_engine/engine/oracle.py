"""Oracle Agent - Predicts consequences of constraint movement."""


class Oracle:
    """Answers: If X changes, what becomes possible?"""

    def __init__(self, graph):
        self.graph = graph

    def predict(self, constraint_id, new_severity):
        return {
            'constraint': constraint_id,
            'new_severity': new_severity,
            'newly_possible': [],
            'accelerated': [],
            'confidence': 0.0,
        }