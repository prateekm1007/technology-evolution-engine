from dataclasses import dataclass, field
@dataclass
class Blueprint:
    blueprint_id: str
    candidate_id: str
    title: str
    bom: list = field(default_factory=list)
    risks: list = field(default_factory=list)
    assumptions: list = field(default_factory=list)
    def to_dict(self): return dict(self.__dict__)
