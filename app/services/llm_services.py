from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate
from app.core.config import settings

def analyze_data_with_llm(data: list[dict]) -> str:
    """
    Menganalisis data menggunakan LLM dan mengembalikan teks analisis.
    
    Args:
        data (list[dict]): Data yang akan dianalisis.
    
    Returns:
        str: Teks analisis dari LLM.
    """
    llm = GoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=settings.GOOGLE_API_KEY)
    prompt_template = PromptTemplate(
        input_variables=["data"],
        template="Anda adalah analis data profesional. Berdasarkan data berikut dalam format list of dictionaries: {data}, berikan analisis tekstual yang sangat singkat dan langsung ke intinya. Fokus pada nilai tertinggi, total, atau tren utama yang terlihat dalam data. Jika data hanya satu entri, sampaikan nilai tersebut. Jika data kosong, beri pesan 'Tidak ada data untuk dianalisis.'"
    )
    chain = prompt_template | llm
    result = chain.invoke({"data": str(data)})
    return result.strip()