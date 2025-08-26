from langsmith import Client
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("LANGCHAIN_API_KEY")
if api_key:
    print(f"API Key loaded: {api_key[:5]}...")  # Debug print
    # Gunakan endpoint default tanpa LANGSMITH_ENDPOINT
    langsmith_client = Client(api_key=api_key)
else:
    print("LANGCHAIN_API_KEY tidak ditemukan - LangSmith tracing disabled")
    langsmith_client = None

__all__ = ["langsmith_client"]