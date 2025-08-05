from sqlalchemy import create_engine, text
from app.core.config import settings

def execute_query(query: str, database_name: str) -> list[dict]:
    """
    Mengeksekusi query SQL di database yang ditentukan dan mengembalikan data.
    
    Args:
        query (str): Query SQL yang akan dieksekusi.
        database_name (str): Nama database yang akan di-query.
    
    Returns:
        list[dict]: List dari baris data dalam bentuk dictionary.
    """
    db_url = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{database_name}"
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text(query))
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in result.fetchall()]
    return data