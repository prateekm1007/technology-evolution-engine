from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from product.orchestration.pipeline import Orchestrator
router = APIRouter()
orchestrator = Orchestrator()
class BusinessRequest(BaseModel):
    raw_text: str
    patent_id: Optional[str] = None
    title: Optional[str] = None
class ConsumerRequest(BaseModel):
    problem_statement: str
    budget_usd: Optional[float] = None
    timeline_days: Optional[int] = None
    skill_level: Optional[str] = 'intermediate'
    domain: Optional[str] = None
class GenericRequest(BaseModel):
    mode: Optional[str] = None
    raw_text: Optional[str] = None
    problem_statement: Optional[str] = None
    patent_id: Optional[str] = None
    budget_usd: Optional[float] = None
@router.post('/api/v1/business/analyze')
def analyze_patent(req: BusinessRequest):
    try: return orchestrator.run({'mode':'business','raw_text':req.raw_text,'patent_id':req.patent_id,'title':req.title})
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
@router.post('/api/v1/consumer/solve')
def solve_problem(req: ConsumerRequest):
    try: return orchestrator.run({'mode':'consumer','problem_statement':req.problem_statement,'budget_usd':req.budget_usd,'timeline_days':req.timeline_days,'skill_level':req.skill_level,'domain':req.domain})
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
@router.post('/api/v1/analyze')
def analyze_generic(req: GenericRequest):
    try: return orchestrator.run({k:v for k,v in req.dict().items() if v is not None})
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
