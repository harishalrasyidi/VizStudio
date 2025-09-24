import uuid
from typing import Optional

def validate_or_generate_session_id(session_id: Optional[str]) -> str:
    """
    Validate session_id as UUID or generate a new one
    
    Args:
        session_id: Optional session ID string
        
    Returns:
        str: Valid UUID string
    """
    if session_id is None:
        # Generate new UUID if not provided
        return str(uuid.uuid4())
    
    try:
        # Validate if it's a valid UUID
        uuid.UUID(session_id)
        return session_id
    except ValueError:
        # If invalid UUID, generate a new one
        return str(uuid.uuid4())

def is_valid_uuid(session_id: str) -> bool:
    """
    Check if session_id is a valid UUID
    
    Args:
        session_id: Session ID string to validate
        
    Returns:
        bool: True if valid UUID, False otherwise
    """
    try:
        uuid.UUID(session_id)
        return True
    except ValueError:
        return False