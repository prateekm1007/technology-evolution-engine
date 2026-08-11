from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
class InputType(Enum):
    PATENT_PDF = 'patent_pdf'
    PATENT_TEXT = 'patent_text'
@dataclass
class PatentInput:
    raw_text: str
    input_type: InputType = InputType.PATENT_TEXT
    patent_id: Optional[str] = None
    claims: list = field(default_factory=list)
    components: list = field(default_factory=list)
    materials: list = field(default_factory=list)
    methods: list = field(default_factory=list)
    constraints: dict = field(default_factory=dict)
    def to_dict(self): return dict(self.__dict__)
