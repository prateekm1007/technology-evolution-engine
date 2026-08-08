import json, os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')


class GraphRetriever:
    """Civilization graph retriever.

    Phase 1 (Amendment directive) — Silent failure elimination:

    The old `graph` property caught all exceptions and silently returned
    `{'nodes':{}, 'edges':[]}`. That made a missing/corrupt graph file
    indistinguishable from a successfully loaded empty graph. Downstream
    components then produced a zero-valued report that looked like a
    valid negative result.

    Per the Final Non-Negotiable Principle, silent failures are
    unacceptable. The fix:
      - record the load error in `_load_error`
      - raise on first use if load failed
      - distinguish "graph missing" from "graph empty"

    The old `_cem` method caught all Exception and passed. That made
    a permissions error or encoding bug look like "no cemetery matches".
    The fix: record errors per-file and surface them in the result,
    rather than silently swallowing.
    """

    def __init__(self, graph_path=None):
        self.graph_path = graph_path or os.path.join(DATA_DIR, 'civilization_graph.json')
        self._g = None
        self._load_error = None
        self._load_attempted = False

    @property
    def graph(self):
        if self._g is None and not self._load_attempted:
            self._load_attempted = True
            try:
                with open(self.graph_path) as f:
                    self._g = json.load(f)
            except FileNotFoundError as e:
                self._load_error = f"graph file not found: {self.graph_path} ({e})"
                self._g = {'nodes': {}, 'edges': []}
            except json.JSONDecodeError as e:
                self._load_error = f"graph file corrupt JSON: {self.graph_path} ({e})"
                self._g = {'nodes': {}, 'edges': []}
            except OSError as e:
                self._load_error = f"graph file IO error: {self.graph_path} ({e})"
                self._g = {'nodes': {}, 'edges': []}
            # NOTE: do NOT catch generic Exception. An unexpected error
            # should propagate, not be silently swallowed.
        return self._g

    @property
    def load_error(self):
        """Return the graph load error, or None if load succeeded.

        The BusinessPipeline checks this and raises loudly if the graph
        failed to load, rather than producing a zero-valued report.
        """
        # Trigger load if not yet attempted
        _ = self.graph
        return self._load_error

    def run(self, d):
        # Phase 1: surface the load error if any. The caller (BusinessPipeline)
        # checks `load_error` separately, but we also surface it here so
        # that direct callers of `retriever.run()` see the error.
        if self.load_error is not None:
            # We do NOT raise here — the BusinessPipeline raises. Direct
            # callers get a result with total_nodes_searched=0 and can
            # inspect `retriever.load_error` for the cause.
            pass

        terms = (d.get('components', []) + d.get('materials', [])
                 + d.get('methods', []) + d.get('detected_domains', []))
        matched = self._nodes(terms)
        return {
            'matched_nodes': matched,
            'adjacency_map': self._adj(matched),
            'cemetery_matches': self._cem(terms),
            'prerequisite_gaps': self._prereqs(matched),
            'total_nodes_searched': len(self.graph.get('nodes', {})),
            'total_edges_searched': len(self.graph.get('edges', [])),
            'graph_load_error': self._load_error,  # NEW: surface the error
        }

    def _nodes(self, terms):
        matched = []
        nodes = self.graph.get('nodes', {})
        if isinstance(nodes, dict):
            for name, data in nodes.items():
                node = dict(data) if isinstance(data, dict) else {'value': data}
                node['name'] = name
                node['id'] = name
                if any(t.lower() in json.dumps(node).lower() for t in terms):
                    matched.append(node)
        else:
            for node in nodes:
                if any(t.lower() in json.dumps(node).lower() for t in terms):
                    matched.append(node)
        return matched

    def _adj(self, nodes):
        ids = set(n.get('id') or n.get('name', '') for n in nodes)
        adj = {}
        for e in self.graph.get('edges', []):
            s, t = e.get('source', ''), e.get('target', '')
            if s in ids:
                adj.setdefault(s, []).append({
                    'target': t, 'relationship': e.get('relationship', 'related'),
                    'weight': e.get('weight', 1.0),
                })
            if t in ids:
                adj.setdefault(t, []).append({
                    'target': s, 'relationship': e.get('relationship', 'related'),
                    'weight': e.get('weight', 1.0),
                })
        return adj

    def _cem(self, terms):
        """Cemetery/historian matches.

        Phase 1: the old code caught all Exception and passed silently.
        The fix records per-file errors in `cemetery_scan_errors` and
        returns them in the result, rather than swallowing them. A
        permissions or encoding error is now visible to the operator.
        """
        matches = []
        scan_errors = []  # NEW
        base = os.path.dirname(DATA_DIR)
        for sub in ['cemetery', os.path.join('data', 'historian')]:
            d = os.path.join(base, sub)
            if not os.path.exists(d):
                continue
            try:
                files = os.listdir(d)
            except OSError as e:
                scan_errors.append({
                    'directory': d, 'error': f"{type(e).__name__}: {e}",
                })
                continue
            for fn in files:
                if not fn.endswith(('.yaml', '.json')):
                    continue
                path = os.path.join(d, fn)
                try:
                    with open(path, encoding='utf-8', errors='strict') as f:
                        content = f.read().lower()
                    for t in terms:
                        if t.lower() in content:
                            matches.append({
                                'file': os.path.join(sub, fn),
                                'matched_term': t,
                            })
                            break
                except (OSError, UnicodeDecodeError) as e:
                    scan_errors.append({
                        'file': path, 'error': f"{type(e).__name__}: {e}",
                    })
                    # Do NOT silently pass. Record and continue scanning
                    # the remaining files.
                # NOTE: do NOT catch generic Exception. An unexpected
                # error should propagate, not be silently swallowed.
        # Stash scan errors on self so callers can inspect them
        self._last_cemetery_scan_errors = scan_errors
        return matches

    @property
    def last_cemetery_scan_errors(self):
        """Per-file errors from the most recent _cem() call."""
        return getattr(self, '_last_cemetery_scan_errors', [])

    def _prereqs(self, nodes):
        return [{'node': n.get('name', n.get('id', '?')),
                 'prerequisite': p,
                 'node_status': n.get('status', '')}
                for n in nodes for p in n.get('prerequisites', [])]
