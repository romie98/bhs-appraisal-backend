"""Authentication API router"""
import logging
import os
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    UserSignup,
    UserLogin,
    GoogleLogin,
    TokenResponse,
    UserResponse
)
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token
)
from app.services.auth_dependency import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    """
    Create a new user account with email and password.
    
    Returns:
        Access token for the newly created user
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    try:
        new_user = User(
            email=user_data.email,
            password_hash=hash_password(user_data.password)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"New user signed up: {user_data.email}")
        
        # Create and return access token
        token = create_access_token({"sub": user_data.email})
        return TokenResponse(access_token=token)
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login with email and password.
    
    Uses OAuth2PasswordRequestForm for compatibility with OAuth2 standard.
    Note: form_data.username is the email, form_data.password is the password.
    
    Returns:
        Access token for authenticated user
    """
    # Find user by email (OAuth2PasswordRequestForm uses 'username' field for email)
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user has a password (Google-only users won't have one)
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account uses Google login. Please sign in with Google.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"User logged in: {user.email}")
    
    # Create and return access token
    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token)


@router.post("/login-json", response_model=TokenResponse)
def login_json(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password using JSON body.
    
    Alternative to /login endpoint that accepts JSON instead of form data.
    
    Returns:
        Access token for authenticated user
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user has a password
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account uses Google login. Please sign in with Google."
        )
    
    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    logger.info(f"User logged in: {user.email}")
    
    # Create and return access token
    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token)


@router.post("/google", response_model=TokenResponse)
def login_with_google(google_data: GoogleLogin, db: Session = Depends(get_db)):
    """
    Login or signup with Google OAuth.
    
    Verifies the Google ID token and creates/updates user account.
    
    Returns:
        Access token for authenticated user
    """
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests
        
        # Verify Google token
        # Note: You'll need to set GOOGLE_CLIENT_ID in environment variables
        GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        
        if not GOOGLE_CLIENT_ID:
            logger.warning("GOOGLE_CLIENT_ID not set. Google login may not work correctly.")
            # For development, we'll try to verify without client ID
            try:
                info = id_token.verify_oauth2_token(
                    google_data.google_token,
                    requests.Request(),
                    GOOGLE_CLIENT_ID
                )
            except:
                # If no client ID, we'll trust the token (not recommended for production)
                import base64
                import json
                # Decode JWT without verification (development only)
                parts = google_data.google_token.split('.')
                if len(parts) == 3:
                    payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
                    info = payload
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid Google token format"
                    )
        else:
            info = id_token.verify_oauth2_token(
                google_data.google_token,
                requests.Request(),
                GOOGLE_CLIENT_ID
            )
        
        email = info.get("email")
        google_id = info.get("sub")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google token missing email"
            )
        
    except Exception as e:
        logger.error(f"Error verifying Google token: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Google token"
        )
    
    # Find or create user
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Create new user
        user = User(
            email=email,
            google_id=google_id,
            password_hash=None  # Google-only users don't have passwords
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"New user created via Google: {email}")
    else:
        # Update Google ID if not set
        if not user.google_id and google_id:
            user.google_id = google_id
            db.commit()
            db.refresh(user)
        logger.info(f"User logged in via Google: {email}")
    
    # Create and return access token
    token = create_access_token({"sub": email})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def get_current_user_info(user: User = Depends(get_current_user)):
    """
    Get current user information.
    
    This endpoint requires authentication via get_current_user dependency.
    """
    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at
    )

