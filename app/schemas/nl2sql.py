from pydantic import BaseModel, Field
from typing import Optional

class NL2SQLRequest(BaseModel):
    """
    Model untuk request NL2SQL.
    
    Attributes:
        prompt (str): Prompt dalam bahasa natural (Bahasa Indonesia)
        database_name (Optional[str]): Nama database yang akan diquery (opsional)
        table_names (Optional[list[str]]): List nama tabel yang relevan (opsional)
    """
    prompt: str = Field(
        ...,
        description="Prompt dalam bahasa natural (Bahasa Indonesia)",
        example="tampilkan total penjualan per kategori tahun 2023"
    )
    database_name: Optional[str] = Field(
        None,
        description="Nama database yang akan diquery (opsional)"
    )
    table_names: Optional[list[str]] = Field(
        None,
        description="List nama tabel yang relevan (opsional)"
    )

class NL2SQLResponse(BaseModel):
    """
    Model untuk response NL2SQL.
    
    Attributes:
        sql_query (str): Query SQL yang dihasilkan
        confidence_score (float): Skor kepercayaan dari model (0-1)
        explanation (Optional[str]): Penjelasan tentang query yang dihasilkan
        analysis (Optional[str]): Analisis tekstual dari data query
    """
    sql_query: str = Field(
        ...,
        description="Query SQL yang dihasilkan",
        example="SELECT category, SUM(sales) as total_sales FROM sales WHERE YEAR(date) = 2023 GROUP BY category"
    )
    confidence_score: float = Field(
        ...,
        description="Skor kepercayaan dari model (0-1)",
        ge=0.0,
        le=1.0,
        example=0.95
    )
    explanation: Optional[str] = Field(
        None,
        description="Penjelasan tentang query yang dihasilkan",
        example="Query ini akan menghitung total penjualan untuk setiap kategori di tahun 2023"
    )
    analysis: Optional[str] = Field(
        None,
        description="Analisis tekstual dari data query",
        example="Berdasarkan data, kategori 'Electronics' memiliki penjualan tertinggi di tahun 2023."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sql_query": "SELECT category, SUM(sales) as total_sales FROM sales WHERE YEAR(date) = 2023 GROUP BY category",
                "confidence_score": 0.95,
                "explanation": "Query ini akan menghitung total penjualan untuk setiap kategori di tahun 2023",
                "analysis": "Berdasarkan data, kategori 'Electronics' memiliki penjualan tertinggi di tahun 2023."
            }
        }