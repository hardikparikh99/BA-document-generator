"""
Database configuration for the CrewAI Multi-Agent Project Documentation System.
This module handles connections to databases and provides utility functions.
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import aiofiles
import asyncio

from utils.config import get_settings
from utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)
settings = get_settings()

class JSONDatabase:
    """
    Simple JSON file-based database for storing application data.
    Used as a lightweight alternative to a full database for development.
    """
    
    def __init__(self, db_name: str):
        """
        Initialize the database.
        
        Args:
            db_name: Name of the database (will be used as filename)
        """
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_dir = os.path.join(self.base_dir, "data")
        
        # Create data directory if it doesn't exist
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
            
        self.db_path = os.path.join(self.db_dir, f"{db_name}.json")
        self.lock = asyncio.Lock()
        
    async def _ensure_db_exists(self):
        """Ensure the database file exists."""
        if not os.path.exists(self.db_path):
            async with aiofiles.open(self.db_path, 'w') as f:
                await f.write(json.dumps({}))
    
    async def _read_db(self) -> Dict[str, Any]:
        """Read the database file."""
        await self._ensure_db_exists()
        async with aiofiles.open(self.db_path, 'r') as f:
            content = await f.read()
            return json.loads(content) if content else {}
    
    async def _write_db(self, data: Dict[str, Any]):
        """Write to the database file."""
        async with aiofiles.open(self.db_path, 'w') as f:
            await f.write(json.dumps(data, default=self._json_serializer))
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for objects not serializable by default json code."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the database.
        
        Args:
            key: Key to retrieve
            
        Returns:
            The value if found, None otherwise
        """
        async with self.lock:
            db = await self._read_db()
            return db.get(key)
    
    async def set(self, key: str, value: Any):
        """
        Set a value in the database.
        
        Args:
            key: Key to set
            value: Value to store
        """
        async with self.lock:
            db = await self._read_db()
            db[key] = value
            await self._write_db(db)
    
    async def delete(self, key: str):
        """
        Delete a key from the database.
        
        Args:
            key: Key to delete
        """
        async with self.lock:
            db = await self._read_db()
            if key in db:
                del db[key]
                await self._write_db(db)
    
    async def list_keys(self) -> List[str]:
        """
        List all keys in the database.
        
        Returns:
            List of keys
        """
        async with self.lock:
            db = await self._read_db()
            return list(db.keys())

# Database instances
file_db = JSONDatabase("files")
transcription_db = JSONDatabase("transcriptions")
documentation_db = JSONDatabase("documentation")
status_db = JSONDatabase("status")
download_db = JSONDatabase("downloads")

async def store_file_metadata(metadata: Dict[str, Any]):
    """
    Store file metadata in the database.
    
    Args:
        metadata: File metadata
    """
    await file_db.set(metadata["file_id"], metadata)

async def get_file_metadata(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Get file metadata from the database.
    
    Args:
        file_id: File ID
        
    Returns:
        File metadata if found, None otherwise
    """
    return await file_db.get(file_id)

async def store_transcription(file_id: str, transcription: str, metadata: Dict[str, Any]):
    """
    Store a transcription in the database.
    
    Args:
        file_id: File ID
        transcription: Transcription text
        metadata: Transcription metadata
    """
    data = {
        "transcription": transcription,
        "metadata": metadata
    }
    await transcription_db.set(file_id, data)

async def get_transcription(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a transcription from the database.
    
    Args:
        file_id: File ID
        
    Returns:
        Transcription data if found, None otherwise
    """
    return await transcription_db.get(file_id)

async def store_documentation(documentation: Dict[str, Any]):
    """
    Store documentation in the database.
    
    Args:
        documentation: Documentation data
    """
    await documentation_db.set(documentation["documentation_id"], documentation)
    # Also store by file_id for easy lookup
    await documentation_db.set(f"file_{documentation['file_id']}", documentation["documentation_id"])

async def get_documentation(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Get documentation by file ID.
    
    Args:
        file_id: File ID
        
    Returns:
        Documentation if found, None otherwise
    """
    doc_id = await documentation_db.get(f"file_{file_id}")
    if doc_id:
        return await documentation_db.get(doc_id)
    return None

async def get_documentation_by_id(doc_id: str) -> Optional[Dict[str, Any]]:
    """
    Get documentation by documentation ID.
    
    Args:
        doc_id: Documentation ID
        
    Returns:
        Documentation if found, None otherwise
    """
    return await documentation_db.get(doc_id)

async def update_processing_status(file_id: str, status: str, progress: int, current_stage: str, error: Optional[str] = None):
    """
    Update the processing status for a file.
    
    Args:
        file_id: File ID
        status: Status (uploaded, processing, completed, failed)
        progress: Progress percentage (0-100)
        current_stage: Current processing stage
        error: Error message if any
    """
    current_data = await status_db.get(file_id) or {}
    current_data.update({
        "file_id": file_id,
        "status": status,
        "progress": progress,
        "current_stage": current_stage,
        "update_time": datetime.now().isoformat()
    })
    
    if error:
        current_data["error"] = error
        
    if "start_time" not in current_data:
        current_data["start_time"] = datetime.now().isoformat()
        
    await status_db.set(file_id, current_data)

async def get_processing_status(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the processing status for a file.
    
    Args:
        file_id: File ID
        
    Returns:
        Status data if found, None otherwise
    """
    return await status_db.get(file_id)

async def store_download_info(download_info: Dict[str, Any]):
    """
    Store download information in the database.
    
    Args:
        download_info: Download information
    """
    key = f"{download_info['file_id']}_{download_info['format']}"
    await download_db.set(key, download_info)

async def get_download_info(file_id: str, format: str) -> Optional[Dict[str, Any]]:
    """
    Get download information from the database.
    
    Args:
        file_id: File ID
        format: Document format
        
    Returns:
        Download information if found, None otherwise
    """
    key = f"{file_id}_{format}"
    return await download_db.get(key)

async def update_processing_status(file_id: str, status: str, progress: int, current_stage: str, error: str = None):
    """
    Update the processing status for a file.
    
    Args:
        file_id: File ID
        status: Status (e.g., 'processing', 'completed', 'failed')
        progress: Progress percentage (0-100)
        current_stage: Current processing stage
        error: Error message if any
    """
    status_data = {
        "file_id": file_id,
        "status": status,
        "progress": progress,
        "current_stage": current_stage,
        "updated_at": datetime.now(),
    }
    
    if error:
        status_data["error"] = error
        
    await status_db.set(file_id, status_data)
    
async def get_processing_status(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the processing status for a file.
    
    Args:
        file_id: File ID
        
    Returns:
        Status information if found, None otherwise
    """
    return await status_db.get(file_id)
