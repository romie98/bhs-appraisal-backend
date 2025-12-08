"""Supabase Storage service for file uploads"""
from supabase import create_client, Client
from fastapi import UploadFile
import uuid
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "uploads")

# Initialize Supabase client
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    logger.warning("Supabase credentials not found in environment variables")
    supabase: Optional[Client] = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        supabase = None


def upload_file_to_supabase(file: UploadFile, folder: str = "") -> Dict:
    """
    Upload a file to Supabase Storage.
    
    Args:
        file: FastAPI UploadFile object
        folder: Optional folder path within the bucket (e.g., "lesson-plans", "photos")
    
    Returns:
        Dictionary with "path" and "filename" on success, or {"error": str} on failure
    """
    if not supabase:
        return {"error": "Supabase client not initialized. Check environment variables."}
    
    try:
        # Get file extension
        file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
        unique_name = f"{uuid.uuid4()}.{file_extension}"
        
        # Build full path
        full_path = f"{folder}/{unique_name}" if folder else unique_name
        
        # Read file content
        file.file.seek(0)  # Reset file pointer
        file_bytes = file.file.read()
        
        # Upload to Supabase Storage
        # Use upsert=True to overwrite if file exists (shouldn't happen with UUID)
        response = supabase.storage.from_(SUPABASE_BUCKET).upload(
            full_path, 
            file_bytes,
            file_options={"content-type": file.content_type or "application/octet-stream", "upsert": "true"}
        )
        
        logger.info(f"File uploaded to Supabase: {full_path}")
        
        # Get public URL for the uploaded file
        try:
            public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(full_path)
            # Remove trailing '?' if present
            if public_url and public_url.endswith("?"):
                public_url = public_url[:-1]
            logger.info(f"Public URL generated: {public_url}")
        except Exception as e:
            logger.warning(f"Could not get public URL, using signed URL instead: {e}")
            # Fallback to signed URL if public URL fails
            public_url = get_signed_url(full_path, expires_in=31536000)  # 1 year expiration
            # Remove trailing '?' if present
            if public_url and public_url.endswith("?"):
                public_url = public_url[:-1]
        
        return {
            "path": full_path,
            "filename": unique_name,
            "url": public_url,
            "bucket": SUPABASE_BUCKET
        }
    
    except Exception as e:
        logger.error(f"Error uploading file to Supabase: {str(e)}", exc_info=True)
        return {"error": str(e)}


def upload_bytes_to_supabase(file_bytes: bytes, filename: str, folder: str = "", content_type: str = "application/octet-stream") -> Dict:
    """
    Upload file bytes to Supabase Storage.
    
    Args:
        file_bytes: File content as bytes
        filename: Original filename (used to determine extension)
        folder: Optional folder path within the bucket
        content_type: MIME type of the file
    
    Returns:
        Dictionary with "path" and "filename" on success, or {"error": str} on failure
    """
    if not supabase:
        return {"error": "Supabase client not initialized. Check environment variables."}
    
    try:
        # Get file extension
        file_extension = filename.split(".")[-1] if "." in filename else ""
        unique_name = f"{uuid.uuid4()}.{file_extension}"
        
        # Build full path
        full_path = f"{folder}/{unique_name}" if folder else unique_name
        
        # Upload to Supabase Storage
        response = supabase.storage.from_(SUPABASE_BUCKET).upload(
            full_path,
            file_bytes,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        
        logger.info(f"File bytes uploaded to Supabase: {full_path}")
        
        # Get public URL for the uploaded file
        try:
            public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(full_path)
            # Remove trailing '?' if present
            if public_url and public_url.endswith("?"):
                public_url = public_url[:-1]
            logger.info(f"Public URL generated: {public_url}")
        except Exception as e:
            logger.warning(f"Could not get public URL, using signed URL instead: {e}")
            # Fallback to signed URL if public URL fails
            public_url = get_signed_url(full_path, expires_in=31536000)  # 1 year expiration
            # Remove trailing '?' if present
            if public_url and public_url.endswith("?"):
                public_url = public_url[:-1]
        
        return {
            "path": full_path,
            "filename": unique_name,
            "url": public_url,
            "bucket": SUPABASE_BUCKET
        }
    
    except Exception as e:
        logger.error(f"Error uploading file bytes to Supabase: {str(e)}", exc_info=True)
        return {"error": str(e)}


def get_public_url(path: str) -> Optional[str]:
    """
    Get a public URL for accessing a file in Supabase Storage.
    
    Args:
        path: Path to the file in Supabase Storage (e.g., "evidence/uuid.pdf")
    
    Returns:
        Public URL string on success, None on failure
    """
    if not supabase:
        logger.error("Supabase client not initialized")
        return None
    
    try:
        public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(path)
        return public_url
    except Exception as e:
        logger.error(f"Error getting public URL for {path}: {str(e)}", exc_info=True)
        return None


def get_signed_url(path: str, expires_in: int = 3600) -> Optional[str]:
    """
    Get a signed URL for accessing a file in Supabase Storage.
    
    Args:
        path: Path to the file in Supabase Storage (e.g., "lesson-plans/uuid.pdf")
        expires_in: URL expiration time in seconds (default: 3600 = 1 hour)
    
    Returns:
        Signed URL string on success, None on failure
    """
    if not supabase:
        logger.error("Supabase client not initialized")
        return None
    
    try:
        response = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(path, expires_in)
        return response.get("signedURL") if isinstance(response, dict) else response
    except Exception as e:
        logger.error(f"Error creating signed URL for {path}: {str(e)}", exc_info=True)
        return None


def delete_file_from_supabase(path: str) -> bool:
    """
    Delete a file from Supabase Storage.
    
    Args:
        path: Path to the file in Supabase Storage
    
    Returns:
        True if successful, False otherwise
    """
    if not supabase:
        logger.error("Supabase client not initialized")
        return False
    
    try:
        supabase.storage.from_(SUPABASE_BUCKET).remove([path])
        logger.info(f"File deleted from Supabase: {path}")
        return True
    except Exception as e:
        logger.error(f"Error deleting file from Supabase {path}: {str(e)}", exc_info=True)
        return False


