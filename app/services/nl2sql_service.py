from typing import Optional, List, Dict, Any
from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from app.core.config import settings
from app.db.utils import get_table_schema, get_table_sample_data
from app.db.chat_database import get_chat_database
from app.services.db_services import get_datasource_info
from app.utils.session_utils import validate_or_generate_session_id
import sqlparse
import re
import logging
import asyncio

logger = logging.getLogger(__name__)

class NL2SQLService:
    def __init__(self):
        # Inisialisasi model Gemini
        self.llm = GoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1  # Rendah untuk hasil yang lebih deterministik
        )
        
        # Get chat database manager
        self.chat_db = get_chat_database()
        
        # Template prompt yang ditingkatkan untuk BI dengan chat history
        self.chat_prompt_template = ChatPromptTemplate.from_messages([
            ("system", """Anda adalah asisten Business Intelligence yang ahli dalam mengonversi pertanyaan bahasa alami dalam bahasa Indonesia menjadi query SQL yang valid dan efisien untuk PostgreSQL. Tujuan Anda adalah menghasilkan query SQL yang dapat digunakan untuk analisis data dan visualisasi Business Intelligence.

KONTEKS DATABASE:
- Nama Database: {database_name}
- Skema: {schema_info}
- Sampel Data: {sample_data}

ATURAN:
1. Hasilkan HANYA query SQL yang valid untuk PostgreSQL, tanpa penjelasan tambahan dalam output.
2. Gunakan nama tabel dan kolom yang TEPAT sesuai skema yang diberikan.
3. Jika tidak ada tabel spesifik yang disebutkan, pilih tabel yang paling relevan berdasarkan prompt dan skema.
4. Pastikan query efisien dan sesuai untuk visualisasi BI (misal, gunakan agregasi, grouping, atau sorting untuk hasil yang jelas).
5. Jika prompt meminta visualisasi (misal, tren, perbandingan, atau total), strukturkan query untuk menghasilkan data yang mudah divisualisasikan.
6. Gunakan best practice SQL: alias yang jelas, join eksplisit, hindari kolom yang tidak ada di skema.
7. Pertimbangkan context dari percakapan sebelumnya untuk memberikan jawaban yang relevan.
8. Jika user merujuk pada query sebelumnya dengan kata "itu", "tersebut", atau "yang tadi", gunakan context dari riwayat chat.

CONTOH:
Prompt: "Top 10 produk terlaris"
SQL: SELECT product_name, SUM(quantity_sold) as total_sold FROM sales GROUP BY product_name ORDER BY total_sold DESC LIMIT 10;

Prompt: "Tampilkan total penjualan per kategori tahun 2023"
SQL: SELECT c.category_name, SUM(s.quantity_sold) as total_sales FROM sales s JOIN categories c ON s.category_id = c.category_id WHERE YEAR(s.sale_date) = 2023 GROUP BY c.category_name;"""),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{user_prompt}")
        ])
        
        # Create chain with output parser
        self.chain = self.chat_prompt_template | self.llm | StrOutputParser()
        
        # Fallback prompt template untuk non-chat mode
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
3. Jika tidak ada tabel spesifik yang disebutkan, pilih tabel yang paling relevan berdasarkan prompt dan skema.
4. Pastikan query efisien dan sesuai untuk visualisasi BI (misal, gunakan agregasi, grouping, atau sorting untuk hasil yang jelas).
5. Jika prompt meminta visualisasi (misal, tren, perbandingan, atau total), strukturkan query untuk menghasilkan data yang mudah divisualisasikan (misal, kolom terbatas, hasil terurut).
6. Gunakan best practice SQL: alias yang jelas, join eksplisit, hindari kolom yang tidak ada di skema.
7. Jika prompt ambigu, buat asumsi logis berdasarkan skema dan sampel data, prioritaskan hasil yang relevan untuk BI.
8. Tangani kasus kompleks seperti join, subquery, atau window function jika diperlukan oleh prompt.

CONTOH:
Prompt: "Top 10 produk terlaris"
SQL: SELECT product_name, SUM(quantity_sold) as total_sold FROM sales GROUP BY product_name ORDER BY total_sold DESC LIMIT 10;

Prompt: "Tampilkan total penjualan per kategori tahun 2023"
SQL: SELECT c.category_name, SUM(s.quantity_sold) as total_sales FROM sales s JOIN categories c ON s.category_id = c.category_id WHERE YEAR(s.sale_date) = 2023 GROUP BY c.category_name;

PROMPT PENGGUNA:
{user_prompt}

SQL Query:"""
        )
        
        # Fallback chain untuk non-chat mode
        self.fallback_chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

    def _get_chat_history_runnable(self, session_id: str):
        """Create a runnable with message history for a specific session"""
        try:
            def get_session_history(session_id: str):
                return self.chat_db.get_chat_history(session_id)
            
            # Create runnable with message history
            with_message_history = RunnableWithMessageHistory(
                self.chain,
                get_session_history,
                input_messages_key="user_prompt",
                history_messages_key="history",
            )
            
            return with_message_history
            
        except Exception as e:
            logger.error(f"Failed to create chat history runnable: {e}")
            return None

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
        headers = data[0].keys()
        sample_text += "| " + " | ".join(headers) + " |\n"
        sample_text += "|" + "|".join(["-" * len(h) for h in headers]) + "|\n"
        
        for row in data:
            sample_text += "| " + " | ".join(str(row[h]) for h in headers) + " |\n"
        
        return sample_text

    def _clean_sql_query(self, raw_query: str, single_line: bool = False) -> str:
        """Membersihkan output query SQL dari backtick, Markdown, dan format ulang untuk kejelasan."""
        cleaned_query = re.sub(r'```sql|```|;+\s*$', '', raw_query)
        cleaned_query = ' '.join(line.strip() for line in cleaned_query.splitlines() if line.strip())
        formatted_query = sqlparse.format(
            cleaned_query,
            reindent=True,
            keyword_case='upper',
            identifier_case='lower',
            indent_width=2,
            use_space_around_operators=True,
            wrap_after=80
        )
        if single_line:
            formatted_query = ' '.join(formatted_query.split())
        return formatted_query.strip()

    async def generate_sql(
        self,
        prompt: str,
        id_datasource: int,
        table_names: Optional[List[str]] = None,
        session_id: Optional[str] = None
    ) -> tuple[str, float]:
        """
        Menghasilkan query SQL dari prompt bahasa natural.
        
        Args:
            prompt: Prompt dalam bahasa Indonesia
            id_datasource: ID unik datasource
            table_names: List nama tabel yang relevan (opsional)
            session_id: ID sesi chat untuk context history (opsional)
            
        Returns:
            tuple[str, float]: (SQL query yang dihasilkan, skor kepercayaan)
        """
        try:
            # Ambil informasi datasource
            datasource_info = get_datasource_info(id_datasource)
            db_name = datasource_info['db_name']
            
            # Validate or generate session_id as UUID
            valid_session_id = validate_or_generate_session_id(session_id)
            logger.info(f"Using session_id: {valid_session_id} (original: {session_id})")
            
            # Dapatkan informasi skema database
            schema = get_table_schema(id_datasource=id_datasource)
            
            # Filter tabel jika table_names disediakan
            if table_names:
                schema = [s for s in schema if s['table_name'] in table_names]
            # Jika table_names tidak disediakan, gunakan semua tabel dan tambahkan instruksi ke prompt
            else:
                original_prompt = prompt
                prompt = f"{prompt} (pilih tabel yang paling relevan dari skema yang diberikan)"

            # Format informasi skema
            schema_info = self._format_schema_info(schema)
            
            # Dapatkan sampel data untuk setiap tabel
            sample_data = ""
            for table in schema:
                table_data = get_table_sample_data(table['table_name'], id_datasource=id_datasource, limit=3)
                sample_data += self._format_sample_data(table['table_name'], table_data)

            # Use chat history if session_id provided
            if valid_session_id:
                sql_query, confidence_score = await self._generate_with_history(
                    prompt, db_name, schema_info, sample_data, valid_session_id
                )
            else:
                sql_query, confidence_score = await self._generate_without_history(
                    prompt, db_name, schema_info, sample_data
                )
                
            return sql_query, confidence_score
                
        except Exception as e:
            logger.error(f"Error in generate_sql: {e}")
            raise

    async def _generate_with_history(
        self, 
        prompt: str, 
        db_name: str, 
        schema_info: str, 
        sample_data: str, 
        session_id: str
    ) -> tuple[str, float]:
        """Generate SQL with chat history context"""
        try:
            # Get runnable with message history - run sync operation in thread pool
            with_history = await asyncio.get_event_loop().run_in_executor(
                None, 
                self._get_chat_history_runnable, 
                session_id
            )
            
            if not with_history:
                logger.warning("Failed to create chat history runnable, falling back to no-history mode")
                return await self._generate_without_history(prompt, db_name, schema_info, sample_data)
            
            # Prepare input for the chain
            input_data = {
                "user_prompt": prompt,
                "database_name": db_name,
                "schema_info": schema_info,
                "sample_data": sample_data
            }
            
            # Invoke with session context - run sync operation in thread pool
            raw_response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: with_history.invoke(
                    input_data,
                    config={"configurable": {"session_id": session_id}}
                )
            )
            
            # Clean and validate the SQL
            cleaned_sql = self._clean_sql_query(raw_response, single_line=False)
            confidence = self._calculate_confidence(cleaned_sql, schema_info)
            
            return cleaned_sql, confidence
            
        except Exception as e:
            logger.error(f"Error generating SQL with history: {e}")
            # Fallback to no-history mode
            return await self._generate_without_history(prompt, db_name, schema_info, sample_data)

    async def _generate_without_history(
        self, 
        prompt: str, 
        db_name: str, 
        schema_info: str, 
        sample_data: str
    ) -> tuple[str, float]:
        """Generate SQL without chat history (fallback mode)"""
        try:
            # Generate SQL using fallback chain
            result = await self.fallback_chain.ainvoke({
                "database_name": db_name,
                "schema_info": schema_info,
                "sample_data": sample_data,
                "user_prompt": prompt
            })
            
            # Extract SQL query dan bersihkan
            sql_query = self._clean_sql_query(result['text'], single_line=False)
            
            # Hitung confidence score
            confidence_score = self._calculate_confidence(sql_query, schema_info)
            
            return sql_query, confidence_score
            
        except Exception as e:
            logger.error(f"Error generating SQL without history: {e}")
            raise

    def _calculate_confidence(self, sql_query: str, schema_info: str) -> float:
        """Calculate confidence score for generated SQL"""
        confidence_score = min(1.0, len(sql_query) / 50)  # Base score
        common_clauses = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY']
        for clause in common_clauses:
            if clause in sql_query.upper():
                confidence_score += 0.1
        confidence_score = min(1.0, confidence_score)
        return confidence_score