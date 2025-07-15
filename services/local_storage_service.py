"""
Local storage service for the CrewAI Multi-Agent Project Documentation System.
This module handles storage and retrieval of transcriptions using local file system.
"""
import os
import json
import uuid
import aiofiles
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from sentence_transformers import SentenceTransformer

from utils.config import get_settings
from utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)
settings = get_settings()

class LocalStorageService:
    """
    Service for storing and retrieving transcriptions using local file system.
    """
    
    def __init__(self):
        """Initialize the Local Storage service."""
        # Force reload settings from environment variables
        from dotenv import load_dotenv
        load_dotenv(override=True)  # Ensures .env is loaded into os.environ
        
        # Local storage settings
        self.transcriptions_dir = os.path.join(os.getcwd(), "data", "transcriptions")
        os.makedirs(self.transcriptions_dir, exist_ok=True)
        
        # Initialize embedding model for semantic search capabilities
        self.embedding_model = None
        self.initialized = False
        
        # Log the loaded configuration
        logger.info(f"Initialized Local Storage Service")
        logger.info(f"Transcriptions directory: {self.transcriptions_dir}")
        
    async def initialize(self) -> bool:
        """
        Initialize the service and embedding model.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        if self.initialized:
            return True
            
        try:
            # Initialize embedding model for semantic search
            logger.info("Loading sentence transformer model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info(f"Embedding dimension: {self.embedding_model.get_sentence_embedding_dimension()}")
            
            self.initialized = True
            logger.info("Local Storage service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Local Storage service: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def store_transcription(
        self, 
        file_id: str, 
        transcription: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Store a transcription as a file in local storage.
        
        Args:
            file_id: Unique identifier for the file
            transcription: The transcription text
            metadata: Metadata for the transcription
            
        Returns:
            dict: Result of the operation with success status
        """
        try:
            # Ensure all metadata values are valid types
            # and replace None values with appropriate defaults
            duration = metadata.get("duration")
            if duration is None:
                duration = 0
                
            language = metadata.get("language")
            if language is None:
                language = "en"
                
            file_type = metadata.get("file_type")
            if file_type is None:
                file_type = "unknown"
                
            speakers = metadata.get("speakers")
            if speakers is None:
                speakers = 1
            
            # Create a JSON object with transcription and metadata
            local_data = {
                "file_id": file_id,
                "vector_id": f"transcription_{file_id}",  # Keep for compatibility
                "transcription": transcription,
                "metadata": {
                    "duration": duration,
                    "language": language,
                    "file_type": file_type,
                    "speakers": speakers,
                    "created_at": metadata.get("created_at", datetime.now().isoformat())
                }
            }
            
            # Generate embedding if model is initialized
            if self.initialized and self.embedding_model:
                try:
                    embedding = self.embedding_model.encode(transcription).tolist()
                    local_data["embedding"] = embedding
                    logger.info(f"Generated embedding for transcription: {file_id}")
                except Exception as embed_error:
                    logger.error(f"Error generating embedding: {str(embed_error)}")
            
            # Save to local file
            local_file_path = os.path.join(self.transcriptions_dir, f"{file_id}.json")
            async with aiofiles.open(local_file_path, 'w') as f:
                await f.write(json.dumps(local_data, indent=2))
            logger.info(f"Successfully stored transcription in local storage: {local_file_path}")
            
            return {
                "success": True,
                "file_id": file_id,
                "local_path": local_file_path
            }
            
        except Exception as e:
            logger.error(f"Error storing transcription: {str(e)}")
            
            return {
                "success": False,
                "message": f"Error storing transcription: {str(e)}"
            }
    
    async def retrieve_transcription(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a transcription by file ID from local storage.
        
        Args:
            file_id: Unique identifier for the file
            
        Returns:
            dict: Transcription data if found, None otherwise
        """
        local_file_path = os.path.join(self.transcriptions_dir, f"{file_id}.json")
        
        # Check if local file exists
        if os.path.exists(local_file_path):
            try:
                logger.info(f"Found transcription in local storage: {local_file_path}")
                async with aiofiles.open(local_file_path, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    return {
                        "transcription": data.get("transcription", ""),
                        "metadata": data.get("metadata", {}),
                        "source": "local_storage"
                    }
            except Exception as local_error:
                logger.error(f"Error reading local transcription file: {str(local_error)}")
                return None
        else:
            logger.warning(f"No transcription found for file_id: {file_id}")
            return None
    
    async def delete_transcription(self, file_id: str) -> bool:
        """
        Delete a transcription from local storage.
        
        Args:
            file_id: Unique identifier for the file
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        local_file_path = os.path.join(self.transcriptions_dir, f"{file_id}.json")
        if os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
                logger.info(f"Successfully deleted transcription from local storage: {local_file_path}")
                return True
            except Exception as local_error:
                logger.error(f"Error deleting transcription from local storage: {str(local_error)}")
                return False
        else:
            logger.warning(f"No transcription found to delete for file_id: {file_id}")
            return False
    
    async def search_transcriptions(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for transcriptions using semantic similarity.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            list: List of matching transcriptions with similarity scores
        """
        # Ensure embedding model is initialized
        if not self.initialized:
            success = await self.initialize()
            if not success:
                logger.error("Failed to initialize embedding model for search")
                return []
        
        try:
            # Encode the query
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Get all transcription files
            results = []
            for filename in os.listdir(self.transcriptions_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.transcriptions_dir, filename)
                    try:
                        async with aiofiles.open(file_path, 'r') as f:
                            content = await f.read()
                            data = json.loads(content)
                            
                            # Calculate similarity if embedding exists
                            similarity = 0
                            if "embedding" in data:
                                # Simple dot product similarity
                                embedding = data["embedding"]
                                similarity = sum(a*b for a, b in zip(query_embedding, embedding))
                            else:
                                # Generate embedding on the fly if not stored
                                transcription = data.get("transcription", "")
                                if transcription:
                                    embedding = self.embedding_model.encode(transcription).tolist()
                                    similarity = sum(a*b for a, b in zip(query_embedding, embedding))
                            
                            results.append({
                                "file_id": data.get("file_id"),
                                "transcription": data.get("transcription", "")[:200] + "...",  # Preview
                                "metadata": data.get("metadata", {}),
                                "similarity": similarity
                            })
                    except Exception as e:
                        logger.error(f"Error processing file {filename} during search: {str(e)}")
            
            # Sort by similarity (highest first) and limit results
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error during transcription search: {str(e)}")
            return []
