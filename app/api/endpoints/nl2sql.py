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
        request: Request body yang berisi prompt, id_datasource, dan parameter opsional
        
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
                inputs={"prompt": request.prompt, "id_datasource": request.id_datasource, "table_names": request.table_names},
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
            id_datasource=request.id_datasource,
            table_names=request.table_names,
            session_id=getattr(request, 'session_id', None)
        )
        
        # Perbarui run dengan output jika tracing berhasil
        if run is not None:
            run.update(
                outputs={"sql_query": sql_query, "confidence_score": confidence_score}
            )

        # Eksekusi query untuk mendapatkan data
        try:
            data = execute_query(sql_query, request.id_datasource)
            analysis = analyze_data_with_llm(data) if data else "Tidak ada data yang tersedia untuk dianalisis."
        except Exception as e:
            logger.error(f"Error executing query {sql_query}: {str(e)}")
            analysis = f"Error: Query gagal dieksekusi. Periksa query: {sql_query}. Error: {str(e)}"

        # Rekomendasi tipe diagram menggunakan LLM
        recommendation = await recommend_chart_type(sql_query, data, request.prompt)

        # Buat response dengan rekomendasi
        return NL2SQLResponse(
            sql_query=sql_query,
            confidence_score=confidence_score,
            explanation=f"Query dibuat dengan confidence score {confidence_score:.2f}",
            analysis=analysis,
            chart_recommendation=recommendation
        )
        
    except Exception as e:
        logger.error(f"Error generating SQL query or analysis: {str(e)}")
        if run is not None:
            run.update(error=str(e))
        raise HTTPException(status_code=500, detail=f"Error generating SQL query or analysis: {str(e)}")


async def recommend_chart_type(sql_query: str, data: list, prompt: str) -> dict:
    """
    Rekomendasikan tipe diagram berdasarkan prompt dan struktur data.
    Menggunakan LLM untuk analisis.
    """
    from langchain_google_genai import GoogleGenerativeAI
    from langchain.prompts import PromptTemplate
    from app.core.config import settings

    llm = GoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1
    )

    # Analisis struktur data
    if not data:
        return {"recommended_type": "table", "reason": "Tidak ada data untuk divisualisasikan."}
    
    columns = list(data[0].keys()) if data else []
    num_columns = len(columns)
    has_numeric = any(isinstance(row.get(columns[1], 0), (int, float)) for row in data[:5]) if num_columns >= 2 else False
    has_time = any("date" in col.lower() or "month" in col.lower() or "year" in col.lower() for col in columns)
    is_single_category = num_columns == 1

    # Prompt untuk LLM
    prompt_template = PromptTemplate(
        input_variables=["prompt", "sql_query", "data_structure", "num_columns", "has_numeric", "has_time", "is_single_category"],
        template="""Berdasarkan prompt pengguna: "{prompt}"
SQL query: {sql_query}
Struktur data: {num_columns} kolom, dengan kolom: {data_structure}
Apakah ada kolom numerik: {has_numeric}
Apakah ada kolom waktu (date/month/year): {has_time}
Apakah satu kolom kategorikal: {is_single_category}

Rekomendasikan tipe diagram yang paling cocok (bar, line, pie, table) dan berikan alasan singkat dalam bahasa Indonesia. Format output: {{"recommended_type": "bar", "reason": "Alasan singkat"}}"""
    )

    chain = prompt_template | llm
    result = chain.invoke({
        "prompt": prompt,
        "sql_query": sql_query,
        "data_structure": ", ".join(columns),
        "num_columns": num_columns,
        "has_numeric": has_numeric,
        "has_time": has_time,
        "is_single_category": is_single_category
    })

    # Parse hasil LLM (asumsikan format JSON sederhana)
    try:
        import json
        recommendation = json.loads(result.strip())
        return recommendation
    except:
        # Fallback berdasarkan aturan sederhana
        if is_single_category:
            return {"recommended_type": "pie", "reason": "Data kategorikal tunggal, cocok untuk distribusi pie chart."}
        elif has_time and has_numeric:
            return {"recommended_type": "line", "reason": "Data memiliki kolom waktu dan numerik, cocok untuk tren line chart."}
        elif num_columns >= 2 and has_numeric:
            return {"recommended_type": "bar", "reason": "Data agregasi dengan kolom kategorikal dan numerik, cocok untuk bar chart."}
        else:
            return {"recommended_type": "table", "reason": "Data kompleks, tampilkan sebagai tabel."}