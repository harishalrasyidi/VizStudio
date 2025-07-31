from pydantic import BaseModel

class NL2SQLRequest(BaseModel):
    prompt: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "tampilkan total penjualan per kategori"
            }
        }

class NL2SQLResponse(BaseModel):
    sql_query: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "sql_query": "SELECT category, SUM(sales) FROM sales_table GROUP BY category"
            }
        }