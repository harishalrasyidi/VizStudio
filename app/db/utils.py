from typing import List, Dict
from sqlalchemy import text
from .database import get_db_connection

def get_table_schema() -> List[Dict]:
    """
    Mendapatkan informasi skema dari semua tabel di database.
    Returns:
        List[Dict]: List dari informasi tabel yang berisi:
            - table_name: Nama tabel
            - columns: List dari informasi kolom (nama, tipe data, constraints)
            - relationships: List dari foreign key relationships
    """
    with get_db_connection() as conn:
        # Query untuk mendapatkan informasi kolom
        column_query = text("""
            SELECT 
                t.table_name,
                c.column_name,
                c.data_type,
                c.column_default,
                c.is_nullable,
                c.character_maximum_length,
                c.numeric_precision,
                c.numeric_scale
            FROM 
                information_schema.tables t
                JOIN information_schema.columns c ON t.table_name = c.table_name
            WHERE 
                t.table_schema = 'public'
                AND t.table_type = 'BASE TABLE'
            ORDER BY 
                t.table_name, 
                c.ordinal_position;
        """)
        
        # Query untuk mendapatkan informasi foreign key
        fk_query = text("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM 
                information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY';
        """)

        # Eksekusi queries
        columns = conn.execute(column_query).fetchall()
        foreign_keys = conn.execute(fk_query).fetchall()

        # Organize data by table
        schema_info = {}
        
        # Process columns
        for col in columns:
            table_name = col.table_name
            if table_name not in schema_info:
                schema_info[table_name] = {
                    "table_name": table_name,
                    "columns": [],
                    "relationships": []
                }
            
            schema_info[table_name]["columns"].append({
                "name": col.column_name,
                "type": col.data_type,
                "nullable": col.is_nullable == "YES",
                "default": col.column_default,
                "max_length": col.character_maximum_length,
                "numeric_precision": col.numeric_precision,
                "numeric_scale": col.numeric_scale
            })

        # Process foreign keys
        for fk in foreign_keys:
            table_name = fk.table_name
            if table_name in schema_info:
                schema_info[table_name]["relationships"].append({
                    "column": fk.column_name,
                    "foreign_table": fk.foreign_table_name,
                    "foreign_column": fk.foreign_column_name
                })

        return list(schema_info.values())

def get_table_sample_data(table_name: str, limit: int = 5) -> List[Dict]:
    """
    Mendapatkan sampel data dari tabel tertentu.
    Args:
        table_name: Nama tabel
        limit: Jumlah baris yang akan diambil
    Returns:
        List[Dict]: List dari baris data
    """
    with get_db_connection() as conn:
        query = text(f"SELECT * FROM {table_name} LIMIT :limit")
        result = conn.execute(query, {"limit": limit}).fetchall()
        return [dict(row) for row in result]