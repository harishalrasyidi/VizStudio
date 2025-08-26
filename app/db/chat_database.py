import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from langchain_postgres import PostgresChatMessageHistory
from typing import Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class ChatDatabaseManager:
    def __init__(self):
        self.chat_db_url = settings.CHAT_DATABASE_URL or settings.DATABASE_URL
        if not self.chat_db_url:
            # Build from individual components if URL not provided
            self.chat_db_url = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        
        # Create engine for chat database
        self.engine = create_engine(
            self.chat_db_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False
        )
        
        # Create session maker
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"Chat database initialized with URL: {self.chat_db_url[:50]}...")

    def get_chat_history(self, session_id: str, table_name: str = "chat_history") -> PostgresChatMessageHistory:
        """
        Get PostgresChatMessageHistory instance for a specific session
        """
        try:
            return PostgresChatMessageHistory(
                connection_string=self.chat_db_url,
                session_id=session_id,
                table_name=table_name
            )
        except Exception as e:
            logger.error(f"Failed to create chat history for session {session_id}: {e}")
            raise

    def get_session(self):
        """Get database session"""
        return self.SessionLocal()

    def close_connection(self):
        """Close database connection"""
        self.engine.dispose()

# Global instance
chat_db_manager = ChatDatabaseManager()

def get_chat_database():
    """Dependency for getting chat database manager"""
    return chat_db_manager
