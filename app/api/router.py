from fastapi import APIRouter
from .endpoints import nl2sql

api_router = APIRouter()

# Include routers dari endpoints
api_router.include_router(nl2sql.router, prefix="/nl2sql", tags=["NL2SQL"])