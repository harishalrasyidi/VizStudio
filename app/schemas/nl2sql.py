from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class NL2SQLRequest(BaseModel):
    prompt: str = Field(..., description="Prompt dalam bahasa natural (Bahasa Indonesia)", example="tampilkan total penjualan per kategori tahun 2023")
    id_datasource: int = Field(..., description="ID unik untuk datasource yang akan diquery", example=123)
    table_names: Optional[List[str]] = Field(None, description="List nama tabel yang relevan (opsional)")
    session_id: Optional[str] = Field(None, description="ID sesi chat untuk context history (opsional)", example="session_123")
    user_id: Optional[int] = Field(None, description="ID user untuk filter knowledge base (opsional)", example=1)

class NL2SQLResponse(BaseModel):
    sql_query: str = Field(..., description="Query SQL yang dihasilkan", example="SELECT category, SUM(sales) as total_sales FROM sales WHERE YEAR(date) = 2023 GROUP BY category")
    confidence_score: float = Field(..., description="Skor kepercayaan dari model (0-1)", ge=0.0, le=1.0, example=0.95)
    explanation: Optional[str] = Field(None, description="Penjelasan tentang query yang dihasilkan", example="Query ini akan menghitung total penjualan untuk setiap kategori di tahun 2023")
    analysis: Optional[str] = Field(None, description="Analisis tekstual dari data query", example="Berdasarkan data, kategori 'Electronics' memiliki penjualan tertinggi di tahun 2023.")
    chart_recommendation: Optional[Dict[str, str]] = Field(None, description="Rekomendasi tipe diagram dari AI", example={"recommended_type": "bar", "reason": "Agregasi per kategori"})

    class Config:
        json_schema_extra = {
            "example": {
                "sql_query": "SELECT category, SUM(sales) as total_sales FROM sales WHERE YEAR(date) = 2023 GROUP BY category",
                "confidence_score": 0.95,
                "explanation": "Query ini akan menghitung total penjualan untuk setiap kategori di tahun 2023",
                "analysis": "Berdasarkan data, kategori 'Electronics' memiliki penjualan tertinggi di tahun 2023.",
                "chart_recommendation": {"recommended_type": "bar", "reason": "Data agregasi dengan kategori, cocok untuk bar chart"}
            }
        }