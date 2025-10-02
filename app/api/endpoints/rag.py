# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from app.services.rag_service import RAGService

# router = APIRouter()

# rag_service = RAGService()

# class EmbeddingRequest(BaseModel):
#     action: str
#     id: int
#     id_datasource: int
#     entry_type: str
#     term: str
#     content: str

# @router.post("/embed")
# async def embed_knowledge(request: EmbeddingRequest):
#     try:
#         if request.action in ['create', 'update']:
#             rag_service.upsert_knowledge(request.dict())
#         elif request.action == 'delete':
#             rag_service.delete_knowledge(request.id)
#         else:
#             raise ValueError("Invalid action")
#         return {"status": "success"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))