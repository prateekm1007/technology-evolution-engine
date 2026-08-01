"""Tests for graph_engine."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.graph_engine import CivilizationGraph


def test_empty_graph():
    g = CivilizationGraph(graph_path='/tmp/test_graph_empty.json')
    assert len(g.nodes) == 0
    assert len(g.edges) == 0


def test_add_node():
    g = CivilizationGraph(graph_path='/tmp/test_graph_add.json')
    g.add_node('test_tech', 'technology', domain='energy')
    assert g.get_node('test_tech') is not None
    assert g.get_node('test_tech')['type'] == 'technology'


def test_add_edge():
    g = CivilizationGraph(graph_path='/tmp/test_graph_edge.json')
    g.add_node('a', 'technology')
    g.add_node('b', 'prerequisite', pcs_score=0.5)
    g.add_edge('a', 'b', 'requires')
    assert len(g.get_edges_from('a')) == 1
    assert g.get_prerequisites('a') == ['b']


def test_pcs_computation():
    g = CivilizationGraph(graph_path='/tmp/test_graph_pcs.json')
    g.add_node('cand', 'candidate')
    g.add_node('p1', 'prerequisite', pcs_score=0.4)
    g.add_node('p2', 'prerequisite', pcs_score=0.6)
    g.add_edge('cand', 'p1', 'requires')
    g.add_edge('cand', 'p2', 'requires')
    assert abs(g.compute_pcs('cand') - 0.5) < 0.001