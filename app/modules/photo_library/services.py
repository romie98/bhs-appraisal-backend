"""Photo Evidence Library service functions (file handling + OCR)"""
import logging
import os
import base64
from pathlib import Path

from openai import OpenAI

logger = logging.getLogger(__name__)

client = OpenAI()

# Base upload directory for photos
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
        print(f"UPLOAD ERROR: {e}")
        logger.error(f"Error saving photo file {filename}: {e}", exc_info=True)
        raise Exception(f"Failed to save photo file: {e}")


def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from an uploaded image using OpenAI Vision instead of Tesseract.
    Works on Railway with no OS dependencies.
    """
    try:
        with open(image_path, "rb") as f:
            img_bytes = f.read()
            b64 = base64.b64encode(img_bytes).decode()

        # Detect MIME type from file extension
        ext = Path(image_path).suffix.lower()
        mime_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".heic": "image/heic",
            ".webp": "image/webp"
        }
        mime_type = mime_type_map.get(ext, "image/jpeg")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all readable text from this image. Return plain text only."},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}}
                    ]
                }
            ],
            temperature=0
        )

        text = response.choices[0].message.content
        return text or ""

    except Exception as e:
        logger.error(f"OpenAI Vision OCR failed: {e}")
        return ""


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