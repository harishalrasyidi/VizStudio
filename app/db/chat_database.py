import os
import psycopg
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
        
        # Create psycopg connection for PostgresChatMessageHistory
        self.psycopg_connection = None
        self._initialize_psycopg_connection()
        
        logger.info(f"Chat database initialized with URL: {self.chat_db_url[:50]}...")

    def _initialize_psycopg_connection(self):
        """Initialize psycopg connection for PostgresChatMessageHistory"""
        try:
            self.psycopg_connection = psycopg.connect(self.chat_db_url)
            logger.info("Psycopg connection established successfully")
        except Exception as e:
            logger.error(f"Failed to establish psycopg connection: {e}")
            raise

    def ensure_chat_table_exists(self, table_name: str = "chat_history"):
        """Ensure chat history table exists"""
        try:
            if self.psycopg_connection:
                PostgresChatMessageHistory.create_tables(self.psycopg_connection, table_name)
                logger.info(f"Chat history table '{table_name}' ensured to exist")
        except Exception as e:
            logger.error(f"Failed to create chat history table: {e}")
            raise

    def get_chat_history(self, session_id: str, table_name: str = "chat_history") -> PostgresChatMessageHistory:
        """
        Get PostgresChatMessageHistory instance for a specific session
        """
        try:
            # Ensure table exists before creating history instance
            self.ensure_chat_table_exists(table_name)
            
            # Create PostgresChatMessageHistory with correct parameter order
            # table_name and session_id are positional-only arguments
            return PostgresChatMessageHistory(
                table_name,                     # positional argument
                session_id,                     # positional argument
                sync_connection=self.psycopg_connection  # keyword argument
            )
        except Exception as e:
            logger.error(f"Failed to create chat history for session {session_id}: {e}")
            raise

    def get_session(self):
        """Get database session"""
        return self.SessionLocal()

    def close_connection(self):
        """Close database connection"""
        if self.psycopg_connection:
            self.psycopg_connection.close()
        self.engine.dispose()

# Global instance
chat_db_manager = ChatDatabaseManager()

def get_chat_database():
    """Dependency for getting chat database manager"""
    return chat_db_manager
