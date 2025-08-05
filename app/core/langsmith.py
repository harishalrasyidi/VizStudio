from langsmith import Client
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("LANGCHAIN_API_KEY")
if not api_key:
    raise ValueError("LANGCHAIN_API_KEY tidak ditemukan di .env")
print(f"API Key loaded: {api_key[:5]}...")  # Debug print

# Gunakan endpoint default tanpa LANGSMITH_ENDPOINT
langsmith_client = Client(api_key=api_key)

__all__ = ["langsmith_client"]