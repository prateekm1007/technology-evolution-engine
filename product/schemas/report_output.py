from dataclasses import dataclass, field
@dataclass
class BusinessReport:
    report_id: str
    blueprints: list = field(default_factory=list)
    assumptions: list = field(default_factory=list)
    confidence: float = 0.0
    def to_dict(self): return dict(self.__dict__)
@dataclass
class ConsumerReport:
    report_id: str
    solutions: list = field(default_factory=list)
    assumptions: list = field(default_factory=list)
    confidence: float = 0.0
    def to_dict(self): return dict(self.__dict__)
