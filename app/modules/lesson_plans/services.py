"""Lesson Plans service functions for file processing"""
import os
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# File upload directory
UPLOAD_DIR = Path("uploads/lesson_plans")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def extract_text_from_file(file_path: str, file_extension: str) -> str:
    """
    Extract text from uploaded file based on file type.
    
    Args:
        file_path: Path to the uploaded file
        file_extension: File extension (e.g., '.pdf', '.docx', '.txt')
    
    Returns:
        Extracted text content
    """
    try:
        ext = file_extension.lower()
        
        if ext == '.txt':
            # Read plain text file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        
        elif ext == '.docx':
            # Extract text from DOCX file
            try:
                from docx import Document
                doc = Document(file_path)
                text_parts = []
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        text_parts.append(paragraph.text)
                return '\n'.join(text_parts)
            except ImportError:
                logger.error("python-docx library not installed. Install with: pip install python-docx")
                raise Exception("DOCX processing requires python-docx library. Please install it.")
        
        elif ext == '.pdf':
            # Extract text from PDF file
            try:
                import PyPDF2
                text_parts = []
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                return '\n'.join(text_parts)
            except ImportError:
                logger.error("PyPDF2 library not installed. Install with: pip install PyPDF2")
                raise Exception("PDF processing requires PyPDF2 library. Please install it.")
        
        else:
            raise Exception(f"Unsupported file type: {ext}. Supported types: .txt, .docx, .pdf")
    
    except Exception as e:
        logger.error(f"Error extracting text from file {file_path}: {str(e)}")
        raise Exception(f"Failed to extract text from file: {str(e)}")


def save_uploaded_file(file_content: bytes, filename: str, teacher_id: str) -> str:
    """
    Save uploaded file to disk.
    
    Args:
        file_content: File content as bytes
        filename: Original filename
        teacher_id: Teacher ID for organizing files
    
    Returns:
        Path to saved file
    """
    try:
        # Create teacher-specific directory
        teacher_dir = UPLOAD_DIR / teacher_id
        teacher_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename to avoid conflicts
        import uuid
        file_ext = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = teacher_dir / unique_filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Return relative path for database storage
        return str(file_path)
    
    except Exception as e:
        logger.error(f"Error saving uploaded file {filename}: {str(e)}")
        raise Exception(f"Failed to save uploaded file: {str(e)}")


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return Path(filename).suffix.lower()




