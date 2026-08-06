"""Graph Engine - Core graph operations for TEE."""

import json
from pathlib import Path

GRAPH_PATH = Path(__file__).parent.parent / 'data' / 'civilization_graph.json'


class CivilizationGraph:
    """Canonical graph of technological civilization."""

    def __init__(self, graph_path=None):
        self.graph_path = Path(graph_path) if graph_path else GRAPH_PATH
        self.nodes = {}
        self.edges = []
        self._load()

    def _load(self):
        if self.graph_path.exists():
            with open(self.graph_path, 'r') as f:
                data = json.load(f)
            self.nodes = data.get('nodes', {})
            self.edges = data.get('edges', [])

    def save(self):
        self.graph_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.graph_path, 'w') as f:
            json.dump({'nodes': self.nodes, 'edges': self.edges}, f, indent=2)

    def add_node(self, node_id, node_type, **props):
        self.nodes[node_id] = {'type': node_type, **props}

    def add_edge(self, source, target, edge_type, **props):
        self.edges.append({'source': source, 'target': target, 'type': edge_type, **props})

    def get_node(self, node_id):
        return self.nodes.get(node_id)

    def get_edges_from(self, node_id):
        return [e for e in self.edges if e['source'] == node_id]

    def get_edges_to(self, node_id):
        return [e for e in self.edges if e['target'] == node_id]

    def get_prerequisites(self, tech_id):
        return [e['target'] for e in self.get_edges_from(tech_id) if e['type'] == 'requires']

    def get_constraints(self, tech_id):
        return [e['target'] for e in self.get_edges_from(tech_id) if e['type'] == 'blocked_by']

    def compute_pcs(self, candidate_id):
        prereqs = self.get_prerequisites(candidate_id)
        if not prereqs:
            return 1.0
        scores = [self.get_node(p).get('pcs_score', 0.0) for p in prereqs if self.get_node(p)]
        return sum(scores) / len(scores) if scores else 0.0


if __name__ == '__main__':
    g = CivilizationGraph()
    print(f'Graph: {len(g.nodes)} nodes, {len(g.edges)} edges')