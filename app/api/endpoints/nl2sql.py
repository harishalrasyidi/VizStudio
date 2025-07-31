from fastapi import APIRouter, HTTPException, Depends
from app.schemas import NL2SQLRequest, NL2SQLResponse
from app.services.nl2sql_service import NL2SQLService

router = APIRouter()
nl2sql_service = NL2SQLService()

@router.post("/convert", response_model=NL2SQLResponse)
async def convert_nl_to_sql(request: NL2SQLRequest) -> NL2SQLResponse:
    """
    Mengkonversi prompt bahasa natural menjadi query SQL.
    
    Args:
        request: Request body yang berisi prompt dan parameter opsional
        
    Returns:
        NL2SQLResponse: Response yang berisi query SQL, skor kepercayaan, dan penjelasan
        
    Raises:
        HTTPException: Jika terjadi error dalam proses konversi
    """
    try:
        # Generate SQL query
        sql_query, confidence_score = await nl2sql_service.generate_sql(
            prompt=request.prompt,
            database_name=request.database_name,
            table_names=request.table_names
        )
        
        # Buat response
        return NL2SQLResponse(
            sql_query=sql_query,
            confidence_score=confidence_score,
            explanation=f"Query dibuat dengan confidence score {confidence_score:.2f}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating SQL query: {str(e)}"
        )