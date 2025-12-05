"""Authentication dependency for protecting routes"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
import os
from app.core.database import get_db
from app.modules.auth.models import User
from app.core.config import settings

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET", settings.SECRET_KEY)
ALGORITHM = settings.ALGORITHM


def get_current_user_email(token: str = Depends(oauth2_scheme)) -> str:
    """
    Extract and verify JWT token, return user email.
    
    This is a dependency that can be used in route handlers to require authentication.
    
    Args:
        token: JWT token from Authorization header (automatically extracted by OAuth2PasswordBearer)
    
    Returns:
        User email from token
    
    Raises:
        HTTPException: If token is invalid, expired, or missing
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return email
    except JWTError:
        raise credentials_exception


def get_current_user(
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from database.
    
    This dependency requires authentication and returns the full User object.
    
    Args:
        email: User email from token (from get_current_user_email dependency)
        db: Database session
    
    Returns:
        User object from database
    
    Raises:
        HTTPException: If user not found in database
    """
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user


# Alias for convenience
get_current_user_email = get_current_user_email


