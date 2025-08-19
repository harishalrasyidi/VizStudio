from typing import Optional, List
from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from app.core.config import settings
from app.db.utils import get_table_schema, get_table_sample_data
import sqlparse
import re

class NL2SQLService:
    def __init__(self):
        # Inisialisasi model Gemini
        self.llm = GoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1  # Rendah untuk hasil yang lebih deterministik
        )
        
        # Template prompt yang ditingkatkan untuk BI
        self.prompt_template = PromptTemplate(
            input_variables=["database_name", "schema_info", "sample_data", "user_prompt"],
            template="""Anda adalah asisten Business Intelligence yang ahli dalam mengonversi pertanyaan bahasa alami dalam bahasa Indonesia menjadi query SQL yang valid dan efisien untuk PostgreSQL. Tujuan Anda adalah menghasilkan query SQL yang dapat digunakan untuk analisis data dan visualisasi Business Intelligence, seperti laporan, dashboard, atau grafik. Query yang dihasilkan harus akurat, menggunakan skema database yang diberikan, dan dioptimalkan untuk performa serta kejelasan hasil untuk visualisasi.

KONTEKS DATABASE:
- Nama Database: {database_name}
- Skema: {schema_info}
- Sampel Data: {sample_data}

ATURAN:
1. Hasilkan HANYA query SQL yang valid untuk PostgreSQL, tanpa penjelasan tambahan dalam output.
2. Gunakan nama tabel dan kolom yang TEPAT sesuai skema yang diberikan.
3. Pastikan query efisien dan sesuai untuk visualisasi BI (misal, gunakan agregasi, grouping, atau sorting untuk hasil yang jelas).
4. Jika prompt meminta visualisasi (misal, tren, perbandingan, atau total), strukturkan query untuk menghasilkan data yang mudah divisualisasikan (misal, kolom terbatas, hasil terurut).
5. Gunakan best practice SQL: alias yang jelas, join eksplisit, hindari kolom yang tidak ada di skema.
6. Jika prompt ambigu, buat asumsi logis berdasarkan skema dan sampel data, prioritaskan hasil yang relevan untuk BI.
7. Tangani kasus kompleks seperti join, subquery, atau window function jika diperlukan oleh prompt.

PROMPT PENGGUNA:
{user_prompt}

SQL Query:"""
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

    def _format_schema_info(self, schema: List[dict]) -> str:
        """Format informasi skema database menjadi string yang mudah dibaca."""
        schema_text = "STRUKTUR DATABASE:\n"
        for table in schema:
            schema_text += f"\nTabel: {table['table_name']}\n"
            schema_text += "Kolom:\n"
            for column in table['columns']:
                nullable = "NULL" if column['nullable'] else "NOT NULL"
                schema_text += f"- {column['name']} ({column['type']}) {nullable}\n"
            
            if table['relationships']:
                schema_text += "Relasi:\n"
                for rel in table['relationships']:
                    schema_text += f"- {rel['column']} -> {rel['foreign_table']}.{rel['foreign_column']}\n"
        
        return schema_text

    def _format_sample_data(self, table_name: str, data: List[dict]) -> str:
        """Format sampel data menjadi string yang mudah dibaca."""
        if not data:
            return f"Tidak ada sampel data untuk tabel {table_name}"
        
        sample_text = f"\nSAMPEL DATA {table_name}:\n"
        # Header
        headers = data[0].keys()
        sample_text += "| " + " | ".join(headers) + " |\n"
        sample_text += "|" + "|".join(["-" * len(h) for h in headers]) + "|\n"
        
        # Data
        for row in data:
            sample_text += "| " + " | ".join(str(row[h]) for h in headers) + " |\n"
        
        return sample_text

    def _clean_sql_query(self, raw_query: str, single_line: bool = False) -> str:
        """Membersihkan output query SQL dari backtick, Markdown, dan format ulang untuk kejelasan."""
        # Hapus backtick, penanda Markdown (```sql atau ```), dan semicolon tambahan
        cleaned_query = re.sub(r'```sql|```|;+\s*$', '', raw_query)
        
        # Hapus baris kosong berlebih dan normalisasi whitespace
        cleaned_query = ' '.join(line.strip() for line in cleaned_query.splitlines() if line.strip())
        
        # Format ulang query menggunakan sqlparse
        formatted_query = sqlparse.format(
            cleaned_query,
            reindent=True,           # Indentasi rapi
            keyword_case='upper',    # Kata kunci SQL huruf besar
            identifier_case='lower', # Identifier huruf kecil
            indent_width=2,          # Indentasi 2 spasi
            use_space_around_operators=True, # Spasi di sekitar operator
            wrap_after=80            # Batas lebar baris
        )
        
        # Jika single_line=True, ubah ke satu baris
        if single_line:
            formatted_query = ' '.join(formatted_query.split())
        
        # Hapus whitespace berlebih di akhir
        return formatted_query.strip()

    async def generate_sql(
        self,
        prompt: str,
        database_name: Optional[str] = None,
        table_names: Optional[List[str]] = None
    ) -> tuple[str, float]:
        """
        Menghasilkan query SQL dari prompt bahasa natural.
        
        Args:
            prompt: Prompt dalam bahasa Indonesia
            database_name: Nama database (opsional)
            table_names: List nama tabel yang relevan (opsional)
            
        Returns:
            tuple[str, float]: (SQL query yang dihasilkan, skor kepercayaan)
        """
        # Dapatkan informasi skema database
        schema = get_table_schema()
        
        # Filter tabel jika specified
        if table_names:
            schema = [s for s in schema if s['table_name'] in table_names]
        
        # Format informasi skema
        schema_info = self._format_schema_info(schema)
        
        # Dapatkan sampel data untuk setiap tabel
        sample_data = ""
        for table in schema:
            table_data = get_table_sample_data(table['table_name'], limit=3)
            sample_data += self._format_sample_data(table['table_name'], table_data)
        
        # Gunakan nama database dari input atau default ke konfigurasi
        db_name = database_name if database_name else settings.DB_NAME
        
        # Generate SQL menggunakan LangChain
        result = await self.chain.ainvoke({
            "database_name": db_name,
            "schema_info": schema_info,
            "sample_data": sample_data,
            "user_prompt": prompt
        })
        
        # Extract SQL query dan bersihkan (default multi-line)
        sql_query = self._clean_sql_query(result['text'], single_line=False)
        
        # Hitung confidence score sederhana
        confidence_score = min(1.0, len(sql_query) / 50)  # Base score
        common_clauses = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY']
        for clause in common_clauses:
            if clause in sql_query.upper():
                confidence_score += 0.1
        confidence_score = min(1.0, confidence_score)
        
        return sql_query, confidence_score