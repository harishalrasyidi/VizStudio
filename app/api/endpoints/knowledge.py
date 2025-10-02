from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

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
        logger.info(f"Received request to generate embedding for content: {request.content[:100]}")
        embedding = model.encode(request.content).tolist()
        logger.info(f"Generated embedding with length: {len(embedding)}")
        if len(embedding) != 768:
            logger.error(f"Invalid embedding length: {len(embedding)}")
            raise HTTPException(status_code=500, detail="Generated embedding has incorrect length")
        return EmbeddingResponse(embedding=embedding)
    except Exception as e:
        logger.error(f"Failed to generate embedding: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")

@router.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy", "model": "paraphrase-mpnet-base-v2"}