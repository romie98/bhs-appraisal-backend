"""Authentication dependency for protecting routes"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
import os
import uuid
from app.core.database import get_db
from app.modules.auth.models import User
from app.core.config import settings

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET", settings.SECRET_KEY)
ALGORITHM = settings.ALGORITHM


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from database.
    
    This dependency requires authentication and returns the full User object.
    Decodes JWT token to get user ID and loads user from database.
    
    Args:
        token: JWT token from Authorization header (automatically extracted by OAuth2PasswordBearer)
        db: Database session
    
    Returns:
        User object from database
    
    Raises:
        HTTPException: If token is invalid, expired, or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        # Convert string to UUID for proper database comparison
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError) as e:
        # ValueError raised if user_id_str is not a valid UUID
        raise credentials_exception
    
    # Query with UUID directly - SQLAlchemy will handle type conversion
    # If database column is UUID type, this works directly
    # If database column is String, SQLAlchemy converts UUID to string automatically
    user = db.query(User).filter(User.id == str(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Ensure current_user.id is a UUID object for consistent comparisons
    # This allows LogEntry.user_id == current_user.id to work correctly
    # even when database columns are UUID type
    user.id = user_id
    
    return user


