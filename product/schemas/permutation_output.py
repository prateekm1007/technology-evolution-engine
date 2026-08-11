from dataclasses import dataclass, field
@dataclass
class PermutationCandidate:
    candidate_id: str
    name: str
    pcs: float = 0.0
    cis: float = 0.0
    feasibility: float = 0.0
    assumptions: list = field(default_factory=list)
    def to_dict(self): return dict(self.__dict__)
