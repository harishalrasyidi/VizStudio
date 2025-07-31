from typing import Optional, List
from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from app.core.config import settings
from app.db.utils import get_table_schema, get_table_sample_data

class NL2SQLService:
    def __init__(self):
        # Inisialisasi model Gemini
        self.llm = GoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1  # Rendah untuk hasil yang lebih deterministik
        )
        
        # Template prompt untuk konversi NL ke SQL
        self.prompt_template = PromptTemplate(
            input_variables=["schema_info", "sample_data", "user_prompt"],
            template="""Kamu adalah SQL expert yang akan mengubah prompt bahasa Indonesia menjadi query SQL yang valid.

KONTEKS DATABASE:
{schema_info}

CONTOH DATA:
{sample_data}

ATURAN:
1. Gunakan nama tabel dan kolom yang TEPAT sesuai skema
2. Hasilkan HANYA query SQL, tanpa penjelasan
3. Pastikan query valid untuk PostgreSQL
4. Gunakan best practice SQL (aliasing, proper joins, dll)
5. Jangan gunakan kolom yang tidak ada di skema

PROMPT: {user_prompt}

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
        
        # Generate SQL menggunakan LangChain
        result = await self.chain.ainvoke({
            "schema_info": schema_info,
            "sample_data": sample_data,
            "user_prompt": prompt
        })
        
        # Extract SQL query dan bersihkan
        sql_query = result['text'].strip()
        
        # Hitung confidence score sederhana berdasarkan panjang query
        # dan keberadaan klausa umum
        confidence_score = min(1.0, len(sql_query) / 50)  # Base score
        common_clauses = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY']
        for clause in common_clauses:
            if clause in sql_query:
                confidence_score += 0.1
        confidence_score = min(1.0, confidence_score)
        
        return sql_query, confidence_score