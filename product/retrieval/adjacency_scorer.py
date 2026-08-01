"""
Adjacency Scorer - Phase 2 of Evidence Phase
Computes Adjacency Score (AS) between a target artifact and candidate nodes.
"""

class AdjacencyScorer:
    def __init__(self, graph_engine):
        self.graph = graph_engine

    def compute_as(self, target_id, candidate_id):
        """
        AS = structural_similarity
           + prerequisite_overlap
           + material_overlap
           + manufacturing_overlap
           + cemetery_overlap
           + ecosystem_overlap
        """
        target = self.graph.get_node(target_id)
        candidate = self.graph.get_node(candidate_id)
        
        if not target or not candidate:
            return 0.0
            
        # Base heuristic weights for demonstration until full graph data is populated
        structural_similarity = 0.2 if target.get('domain') == candidate.get('domain') else 0.0
        prerequisite_overlap = 0.2 # Requires graph edge intersection analysis
        material_overlap = 0.1
        manufacturing_overlap = 0.1
        cemetery_overlap = 0.2 if candidate.get('type') == 'cemetery' else 0.0
        ecosystem_overlap = 0.2
        
        as_score = (
            structural_similarity +
            prerequisite_overlap +
            material_overlap +
            manufacturing_overlap +
            cemetery_overlap +
            ecosystem_overlap
        )
        return round(as_score, 3)

    def rank_adjacencies(self, target_id, candidate_ids):
        scored = [{"candidate_id": cid, "AS": self.compute_as(target_id, cid)} for cid in candidate_ids]
        return sorted(scored, key=lambda x: x["AS"], reverse=True)
