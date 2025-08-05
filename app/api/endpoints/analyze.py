from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.db_services import execute_query
from app.services.llm_services import analyze_data_with_llm

router = APIRouter()

class AnalyzeRequest(BaseModel):
    query: str
    database_name: str

@router.post("/analyze")
async def analyze_data(request: AnalyzeRequest):
    """
    Mengeksekusi query SQL, mengambil data, dan menganalisisnya dengan LLM.
    
    Args:
        request (AnalyzeRequest): Request body yang berisi query SQL dan nama database.
    
    Returns:
        dict: Teks analisis dari LLM.
    """
    try:
        data = execute_query(request.query, request.database_name)
        analysis = analyze_data_with_llm(data)
        return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))