from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

try:
    model = SentenceTransformer('paraphrase-mpnet-base-v2')  # Dimensi 768
    logger.info("Successfully loaded paraphrase-mpnet-base-v2 model")
except Exception as e:
    logger.error(f"Failed to load SentenceTransformer model: {e}")
    raise

class EmbeddingRequest(BaseModel):
    content: str

class EmbeddingResponse(BaseModel):
    embedding: list[float]

@router.post("/embed", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest):
    try:
        logger.info(f"Generating embedding for content: {request.content}")
        embedding = model.encode(request.content).tolist()
        logger.info(f"Embedding generated with length: {len(embedding)}")
        return EmbeddingResponse(embedding=embedding)
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))