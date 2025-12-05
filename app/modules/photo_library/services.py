"""Photo Evidence Library service functions (file handling + OCR)"""
import logging
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)

# Base upload directory for photos
PHOTO_UPLOAD_DIR = Path("uploads/photos")
PHOTO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def save_photo_file(file_content: bytes, filename: str, teacher_id: str) -> str:
    """Save uploaded photo to disk and return relative file path."""
    try:
        teacher_dir = PHOTO_UPLOAD_DIR / teacher_id
        teacher_dir.mkdir(parents=True, exist_ok=True)

        import uuid

        ext = Path(filename).suffix.lower()
        unique_name = f"{uuid.uuid4()}{ext}"
        file_path = teacher_dir / unique_name

        with open(file_path, "wb") as f:
            f.write(file_content)

        return str(file_path)
    except Exception as e:
        logger.error(f"Error saving photo file {filename}: {e}", exc_info=True)
        raise Exception(f"Failed to save photo file: {e}")


def extract_text_from_image(image_path: str) -> str:
    """Run OCR on the image using pytesseract and return extracted text."""
    try:
        try:
            import pytesseract
            import os
            import platform
            
            # Set Tesseract path for Windows if needed
            if platform.system() == "Windows":
                tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                if os.path.exists(tesseract_path):
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                else:
                    logger.warning(f"Tesseract not found at {tesseract_path}. Trying system PATH...")
        except ImportError:
            logger.error("pytesseract library not installed. Install with: pip install pytesseract")
            raise Exception("OCR requires pytesseract. Please install it on the backend.")

        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        if not text:
            return ""

        # Basic cleaning
        cleaned = text.replace("\r", " ").replace("\t", " ")
        cleaned = "\n".join(line.strip() for line in cleaned.splitlines() if line.strip())
        return cleaned.strip()
    except Exception as e:
        logger.error(f"Error running OCR on {image_path}: {e}", exc_info=True)
        raise Exception(f"Failed to extract text from image: {e}")


def get_image_extension(filename: str) -> str:
    """Return lowercase file extension for an image filename."""
    return Path(filename).suffix.lower()

{
  "cells": [],
  "metadata": {
    "language_info": {
      "name": "python"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 2
}