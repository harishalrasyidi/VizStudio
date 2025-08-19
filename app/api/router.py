from fastapi import APIRouter
from .endpoints import nl2sql, analyze

api_router = APIRouter()

api_router.include_router(nl2sql.router, prefix="/nl2sql", tags=["NL2SQL"])
api_router.include_router(analyze.router, prefix="/analyze", tags=["Analyze"])