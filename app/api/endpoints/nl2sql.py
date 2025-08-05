from fastapi import APIRouter, HTTPException, Depends
from app.schemas import NL2SQLRequest, NL2SQLResponse
from app.services.nl2sql_service import NL2SQLService
from app.services.db_services import execute_query
from app.services.llm_services import analyze_data_with_llm
from app.core.langsmith import langsmith_client
import logging

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
nl2sql_service = NL2SQLService()

@router.post("/convert", response_model=NL2SQLResponse)
async def convert_nl_to_sql(request: NL2SQLRequest) -> NL2SQLResponse:
    """
    Mengkonversi prompt bahasa natural menjadi query SQL dan memberikan analisis tekstual.
    
    Args:
        request: Request body yang berisi prompt dan parameter opsional
        
    Returns:
        NL2SQLResponse: Response yang berisi query SQL, skor kepercayaan, penjelasan, dan analisis tekstual
        
    Raises:
        HTTPException: Jika terjadi error dalam proses konversi atau analisis
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
                run = None
        except Exception as e:
            logger.warning(f"Gagal menghubungkan ke LangSmith: {str(e)}, melanjutkan tanpa tracing.")
            run = None

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

        # Eksekusi query untuk mendapatkan data
        db_name = request.database_name if request.database_name else db_name
        try:
            data = execute_query(sql_query, db_name)
            analysis = analyze_data_with_llm(data) if data else "Tidak ada data yang tersedia untuk dianalisis."
        except Exception as e:
            logger.error(f"Error executing query {sql_query}: {str(e)}")
            analysis = f"Error: Query gagal dieksekusi. Periksa query: {sql_query}. Error: {str(e)}"

        # Buat response
        return NL2SQLResponse(
            sql_query=sql_query,
            confidence_score=confidence_score,
            explanation=f"Query dibuat dengan confidence score {confidence_score:.2f}",
            analysis=analysis
        )
        
    except Exception as e:
        logger.error(f"Error generating SQL query or analysis: {str(e)}")
        if run is not None:
            run.update(error=str(e))
        raise HTTPException(status_code=500, detail=f"Error generating SQL query or analysis: {str(e)}")