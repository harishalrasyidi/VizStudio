from sqlalchemy import create_engine, text
from fastapi import HTTPException
from app.db.database import get_db_connection
from app.core.config import settings

def get_datasource_info(id_datasource: int) -> dict:
    """
    Mengambil detail koneksi datasource dari tabel datasource di database toolsBI.
    
    Args:
        id_datasource (int): ID unik datasource.
    
    Returns:
        dict: Informasi koneksi (host, port, db_name, user, password).
    
    Raises:
        HTTPException: Jika datasource tidak ditemukan.
    """
    try:
        with get_db_connection() as conn:
            query = text("""
                SELECT host, port, database_name, username, password 
                FROM datasources 
                WHERE id_datasource = :id_datasource
            """)
            result = conn.execute(query, {"id_datasource": id_datasource}).fetchone()
            if not result:
                raise HTTPException(status_code=404, detail=f"Datasource {id_datasource} not found")
            return {
                "host": result.host,
                "port": result.port,
                "db_name": result.database_name,
                "user": result.username,
                "password": result.password
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching datasource info: {str(e)}")

def execute_query(query: str, id_datasource: int) -> list[dict]:
    """
    Mengeksekusi query SQL di database berdasarkan id_datasource.
    
    Args:
        query (str): Query SQL yang akan dieksekusi.
        id_datasource (int): ID unik datasource.
    
    Returns:
        list[dict]: List dari baris data dalam bentuk dictionary.
    
    Raises:
        HTTPException: Jika gagal mengeksekusi query.
    """
    try:
        # Ambil detail koneksi dari tabel datasource
        datasource_info = get_datasource_info(id_datasource)
        db_url = (
            f"postgresql://{datasource_info['user']}:{datasource_info['password']}@"
            f"{datasource_info['host']}:{datasource_info['port']}/{datasource_info['db_name']}"
        )
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text(query))
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in result.fetchall()]
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing query: {str(e)}")