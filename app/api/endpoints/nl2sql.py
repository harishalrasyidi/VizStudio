from fastapi import APIRouter, HTTPException, Depends
from app.schemas import NL2SQLRequest, NL2SQLResponse
from app.services.nl2sql_service import NL2SQLService
from app.core.langsmith import langsmith_client  # Impor variabel global
import logging

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    run = None
    try:
        # Coba buat run untuk tracing (opsional)
        try:
            run = langsmith_client.create_run(
                name="nl2sql_conversion",
                inputs={"prompt": request.prompt, "database_name": request.database_name, "table_names": request.table_names},
                run_type="chain"
            )
            if run is None:
                logger.warning("Gagal membuat LangSmith run, melanjutkan tanpa tracing.")
                run = None  # Lanjutkan tanpa tracing
        except Exception as e:
            logger.warning(f"Gagal menghubungkan ke LangSmith: {str(e)}, melanjutkan tanpa tracing.")
            run = None  # Abaikan error LangSmith

        # Generate SQL query
        sql_query, confidence_score = await nl2sql_service.generate_sql(
            prompt=request.prompt,
            database_name=request.database_name,
            table_names=request.table_names
        )
        
        # Perbarui run dengan output jika tracing berhasil
        if run is not None:
            run.update(
                outputs={"sql_query": sql_query, "confidence_score": confidence_score}
            )
        
        # Buat response
        return NL2SQLResponse(
            sql_query=sql_query,
            confidence_score=confidence_score,
            explanation=f"Query dibuat dengan confidence score {confidence_score:.2f}"
        )
        
    except Exception as e:
        # Log error dan perbarui run jika tersedia
        logger.error(f"Error generating SQL query: {str(e)}")
        if run is not None:
            run.update(error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error generating SQL query: {str(e)}"
        )