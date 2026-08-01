import json, os
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
class GraphRetriever:
    def __init__(self, graph_path=None):
        self.graph_path = graph_path or os.path.join(DATA_DIR, 'civilization_graph.json')
        self._g = None
    @property
    def graph(self):
        if self._g is None:
            try:
                with open(self.graph_path) as f: self._g = json.load(f)
            except Exception: self._g = {'nodes':{},'edges':[]}
        return self._g
    def run(self, d):
        terms = d.get('components',[])+d.get('materials',[])+d.get('methods',[])+d.get('detected_domains',[])
        matched = self._nodes(terms)
        return {'matched_nodes':matched,'adjacency_map':self._adj(matched),'cemetery_matches':self._cem(terms),'prerequisite_gaps':self._prereqs(matched),'total_nodes_searched':len(self.graph.get('nodes',{})),'total_edges_searched':len(self.graph.get('edges',[]))}
    def _nodes(self, terms):
        matched = []
        nodes = self.graph.get('nodes', {})
        if isinstance(nodes, dict):
            for name, data in nodes.items():
                node = dict(data) if isinstance(data, dict) else {'value': data}
                node['name'] = name; node['id'] = name
                if any(t.lower() in json.dumps(node).lower() for t in terms): matched.append(node)
        else:
            for node in nodes:
                if any(t.lower() in json.dumps(node).lower() for t in terms): matched.append(node)
        return matched
    def _adj(self, nodes):
        ids = set(n.get('id') or n.get('name','') for n in nodes)
        adj = {}
        for e in self.graph.get('edges',[]):
            s,t = e.get('source',''),e.get('target','')
            if s in ids: adj.setdefault(s,[]).append({'target':t,'relationship':e.get('relationship','related'),'weight':e.get('weight',1.0)})
            if t in ids: adj.setdefault(t,[]).append({'target':s,'relationship':e.get('relationship','related'),'weight':e.get('weight',1.0)})
        return adj
    def _cem(self, terms):
        matches = []
        base = os.path.dirname(DATA_DIR)
        for sub in ['cemetery', os.path.join('data','historian')]:
            d = os.path.join(base, sub)
            if not os.path.exists(d): continue
            for fn in os.listdir(d):
                if not fn.endswith(('.yaml','.json')): continue
                try:
                    content = open(os.path.join(d,fn)).read().lower()
                    for t in terms:
                        if t.lower() in content: matches.append({'file':os.path.join(sub,fn),'matched_term':t}); break
                except Exception: pass
        return matches
    def _prereqs(self, nodes):
        return [{'node':n.get('name',n.get('id','?')),'prerequisite':p,'node_status':n.get('status','')} for n in nodes for p in n.get('prerequisites',[])]
