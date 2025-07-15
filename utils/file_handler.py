"""
File handling utilities for the CrewAI Multi-Agent Project Documentation System.
This module provides functions for file validation, storage, and cleanup.
"""
import os
import uuid
import shutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
import mimetypes
from fastapi import UploadFile
import aiofiles
import asyncio

from .config import get_settings, get_temp_dir
from .logger import setup_logger

# Setup logger
logger = setup_logger(__name__)
settings = get_settings()

# Valid file extensions and their MIME types
VALID_EXTENSIONS = {
    # Video formats
    '.mp4': 'video/mp4',
    '.avi': 'video/x-msvideo',
    '.mov': 'video/quicktime',
    '.mkv': 'video/x-matroska',
    # Audio formats
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.m4a': 'audio/m4a',
    '.flac': 'audio/flac'
}

def is_valid_file_type(filename: str) -> bool:
    """
    Check if a file has a valid extension.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        bool: True if the file has a valid extension, False otherwise
    """
    ext = os.path.splitext(filename)[1].lower()
    return ext in VALID_EXTENSIONS

def is_valid_file_size(file_size: int) -> bool:
    """
    Check if a file is within the maximum allowed size.
    
    Args:
        file_size: Size of the file in bytes
        
    Returns:
        bool: True if the file is within the size limit, False otherwise
    """
    return file_size <= settings.max_file_size_bytes

def generate_file_id() -> str:
    """
    Generate a unique file ID.
    
    Returns:
        str: Unique file ID
    """
    return str(uuid.uuid4())

def get_file_path(file_id: str, filename: str) -> str:
    """
    Get the path where a file should be stored.
    
    Args:
        file_id: Unique identifier for the file
        filename: Original filename
        
    Returns:
        str: Path where the file should be stored
    """
    ext = os.path.splitext(filename)[1].lower()
    return os.path.join(get_temp_dir(), f"{file_id}{ext}")

async def save_uploaded_file(upload_file: UploadFile) -> Dict[str, Any]:
    """
    Save an uploaded file to the temporary directory.
    
    Args:
        upload_file: The uploaded file
        
    Returns:
        dict: Result of the operation with file_id, file_path, and success status
    """
    try:
        # Validate file type
        if not is_valid_file_type(upload_file.filename):
            return {
                "success": False,
                "message": f"Invalid file type. Supported formats: {', '.join(VALID_EXTENSIONS.keys())}"
            }
        
        # Generate file ID
        file_id = generate_file_id()
        
        # Get file path
        file_path = get_file_path(file_id, upload_file.filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as out_file:
            # Read file in chunks to handle large files
            chunk_size = 1024 * 1024  # 1MB chunks
            while content := await upload_file.read(chunk_size):
                await out_file.write(content)
        
        # Check file size after saving
        file_size = os.path.getsize(file_path)
        if not is_valid_file_size(file_size):
            # Remove file if it's too large
            os.remove(file_path)
            return {
                "success": False,
                "message": f"File too large. Maximum size: {settings.max_file_size}"
            }
        
        # Schedule file cleanup
        asyncio.create_task(schedule_file_cleanup(file_path))
        
        return {
            "success": True,
            "file_id": file_id,
            "file_path": file_path,
            "original_filename": upload_file.filename,
            "file_size": file_size
        }
        
    except Exception as e:
        logger.error(f"Error saving uploaded file: {str(e)}")
        return {
            "success": False,
            "message": f"Error saving file: {str(e)}"
        }

async def schedule_file_cleanup(file_path: str, hours: int = None):
    """
    Schedule a file for cleanup after a specified number of hours.
    
    Args:
        file_path: Path to the file to clean up
        hours: Number of hours after which to clean up the file. If None, uses the default from settings.
    """
    if hours is None:
        hours = settings.temp_file_retention
    
    # Sleep for the specified duration
    await asyncio.sleep(hours * 3600)
    
    # Check if file still exists and remove it
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {str(e)}")

def clean_expired_files():
    """
    Clean up expired temporary files.
    This function can be called periodically to remove files older than the retention period.
    """
    temp_dir = get_temp_dir()
    retention_hours = settings.temp_file_retention
    cutoff_time = datetime.now() - timedelta(hours=retention_hours)
    
    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        
        # Skip directories
        if os.path.isdir(file_path):
            continue
        
        # Check file modification time
        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        if mod_time < cutoff_time:
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up expired file: {file_path}")
            except Exception as e:
                logger.error(f"Error cleaning up expired file {file_path}: {str(e)}")

def is_video_file(file_path: str) -> bool:
    """
    Check if a file is a video file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        bool: True if the file is a video file, False otherwise
    """
    ext = os.path.splitext(file_path)[1].lower()
    mime_type = VALID_EXTENSIONS.get(ext)
    return mime_type and mime_type.startswith('video/')

def is_audio_file(file_path: str) -> bool:
    """
    Check if a file is an audio file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        bool: True if the file is an audio file, False otherwise
    """
    ext = os.path.splitext(file_path)[1].lower()
    mime_type = VALID_EXTENSIONS.get(ext)
    return mime_type and mime_type.startswith('audio/')
