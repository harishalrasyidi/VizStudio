from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from app.db.chat_database import get_chat_database
from app.schemas.nl2sql import NL2SQLRequest
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """
    Get chat messages for a specific session
    """
    try:
        chat_db = get_chat_database()
        history = chat_db.get_chat_history(session_id)
        
        # Get messages from PostgresChatMessageHistory
        messages = history.messages
        
        return {
            "status": "success",
            "session_id": session_id,
            "messages": [
                {
                    "type": msg.type,
                    "content": msg.content,
                    "timestamp": getattr(msg, 'timestamp', None)
                }
                for msg in messages
            ],
            "total": len(messages)
        }
        
    except Exception as e:
        logger.error(f"Failed to get session messages: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve session messages: {str(e)}"
        )

@router.delete("/sessions/{session_id}/clear")
async def clear_session_history(session_id: str):
    """
    Clear chat history for a specific session
    """
    try:
        chat_db = get_chat_database()
        history = chat_db.get_chat_history(session_id)
        
        # Clear the history
        history.clear()
        
        return {
            "status": "success",
            "message": f"Session {session_id} history cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear session history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear session history: {str(e)}"
        )

@router.post("/sessions/{session_id}/test")
async def test_session_functionality(session_id: str, request: NL2SQLRequest):
    """
    Test session functionality by adding a test message
    """
    try:
        chat_db = get_chat_database()
        history = chat_db.get_chat_history(session_id)
        
        # Add test messages
        from langchain_core.messages import HumanMessage, AIMessage
        
        human_msg = HumanMessage(content=request.prompt)
        ai_msg = AIMessage(content="Test response from AI")
        
        history.add_message(human_msg)
        history.add_message(ai_msg)
        
        return {
            "status": "success",
            "message": f"Test messages added to session {session_id}",
            "session_id": session_id,
            "messages_count": len(history.messages)
        }
        
    except Exception as e:
        logger.error(f"Failed to test session functionality: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test session: {str(e)}"
        )
