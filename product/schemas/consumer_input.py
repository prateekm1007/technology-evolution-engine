from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
class SkillLevel(Enum):
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
@dataclass
class ConsumerInput:
    problem_statement: str
    budget_usd: Optional[float] = None
    skill_level: SkillLevel = SkillLevel.INTERMEDIATE
    domain: Optional[str] = None
    def to_dict(self): return dict(self.__dict__)
