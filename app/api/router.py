from fastapi import APIRouter
from .endpoints import nl2sql, analyze, chat, knowledge

api_router = APIRouter()

api_router.include_router(nl2sql.router, prefix="/nl2sql", tags=["NL2SQL"])
api_router.include_router(analyze.router, prefix="/analyze", tags=["Analyze"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])