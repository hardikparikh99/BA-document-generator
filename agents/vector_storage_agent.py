"""
Vector Storage Agent for the CrewAI Multi-Agent Project Documentation System.
This agent handles storing and retrieving transcriptions from local storage.
"""
import os
from typing import Dict, Any, Optional, List
import asyncio

from crewai import Agent, Task
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from utils.config import get_settings
from utils.logger import get_agent_logger
from services.local_storage_service import LocalStorageService
from models.database import update_processing_status

# Setup logger
logger = get_agent_logger("vector_storage")
settings = get_settings()

class LocalStorageTool(BaseTool):
    """Tool for storing transcriptions in local storage."""
    
    name: str = "local_storage_tool"
    description: str = "Stores transcriptions in local file system"
    storage_service: LocalStorageService = None
    
    def __init__(self):
        """Initialize the local storage tool."""
        super().__init__()
        self.storage_service = LocalStorageService()
    
    async def _arun(self, file_id: str, transcription: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store a transcription in local storage.
        
        Args:
            file_id: Unique identifier for the file
            transcription: The transcription text
            metadata: Metadata for the transcription
            
        Returns:
            dict: Result of the operation
        """
        return await self.storage_service.store_transcription(
            file_id, 
            transcription, 
            metadata
        )
    
    def _run(self, file_id: str, transcription: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous run method (required by BaseTool)."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(file_id, transcription, metadata))

class EmbeddingTool(BaseTool):
    """Tool for generating embeddings for text."""
    
    name: str = "embedding_tool"
    description: str = "Generates embeddings for text using sentence-transformers"
    storage_service: LocalStorageService = None
    
    def __init__(self):
        """Initialize the embedding tool."""
        super().__init__()
        self.storage_service = LocalStorageService()
    
    async def _arun(self, text: str) -> Dict[str, Any]:
        """
        Generate an embedding for text.
        This is a placeholder as the actual embedding is handled by LocalStorageService.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            dict: Result of the operation
        """
        # Initialize storage service
        await self.storage_service.initialize()
        
        # This is a placeholder as the actual embedding is handled by LocalStorageService
        return {
            "success": True,
            "message": "Embedding generated successfully"
        }
    
    def _run(self, text: str) -> Dict[str, Any]:
        """Synchronous run method (required by BaseTool)."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(text))

class VectorStorageAgent:
    """
    Agent responsible for storing and retrieving transcriptions from local storage.
    """
    
    def __init__(self):
        """Initialize the Vector Storage Agent."""
        self.logger = logger
        self.storage_service = LocalStorageService()
        
        # Create tools
        self.storage_tool = LocalStorageTool()
        self.embedding_tool = EmbeddingTool()
        
        # Create CrewAI agent
        self.agent = Agent(
            role="Storage Manager",
            goal="Store and retrieve transcriptions from local storage",
            backstory="Expert in data storage and information retrieval",
            verbose=True,
            tools=[]
        )
        
        # Add tools to agent after initialization
        self.agent.tools = [self.storage_tool, self.embedding_tool]
    
    async def store_transcription(self, file_id: str, transcription: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store a transcription in local storage.
        
        Args:
            file_id: Unique identifier for the file
            transcription: The transcription text
            metadata: Metadata for the transcription
            
        Returns:
            dict: Result of the operation with file_id and local_path
        """
        try:
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="processing",
                progress=60,
                current_stage="storage"
            )
            
            # Store the transcription
            result = await self.storage_service.store_transcription(
                file_id, 
                transcription, 
                metadata
            )
            
            if result["success"]:
                self.logger.info(f"Transcription stored successfully: {file_id}")
                
                # Update processing status
                await update_processing_status(
                    file_id=file_id,
                    status="processing",
                    progress=70,
                    current_stage="vectorization"
                )
                
                return {
                    "success": True,
                    "file_id": result["file_id"],
                    "local_path": result.get("local_path", "")
                }
            else:
                self.logger.error(f"Transcription storage failed: {result.get('message', 'Unknown error')}")
                
                # Update processing status
                await update_processing_status(
                    file_id=file_id,
                    status="failed",
                    progress=0,
                    current_stage="storage",
                    error=result.get("message", "Unknown error")
                )
                
                return {
                    "success": False,
                    "message": result.get("message", "Unknown error")
                }
            
        except Exception as e:
            self.logger.error(f"Error in store_transcription: {str(e)}")
            
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="failed",
                progress=0,
                current_stage="storage",
                error=str(e)
            )
            
            return {
                "success": False,
                "message": f"Error storing transcription: {str(e)}"
            }
    
    async def retrieve_transcription(self, file_id: str) -> Dict[str, Any]:
        """
        Retrieve a transcription from local storage.
        
        Args:
            file_id: Unique identifier for the file
            
        Returns:
            dict: Result of the operation with transcription and metadata
        """
        try:
            # Retrieve the transcription
            result = await self.storage_service.retrieve_transcription(file_id)
            
            if result:
                self.logger.info(f"Transcription retrieved successfully: {file_id}")
                return {
                    "success": True,
                    "transcription": result["transcription"],
                    "metadata": result["metadata"]
                }
            else:
                self.logger.error(f"Transcription not found: {file_id}")
                return {
                    "success": False,
                    "message": "Transcription not found"
                }
            
        except Exception as e:
            self.logger.error(f"Error in retrieve_transcription: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving transcription: {str(e)}"
            }
    
    def create_task(self, file_id: str, transcription: str, metadata: Dict[str, Any]) -> Task:
        """
        Create a CrewAI task for storing a transcription.
        
        Args:
            file_id: Unique identifier for the file
            transcription: The transcription text
            metadata: Metadata for the transcription
            
        Returns:
            Task: CrewAI task
        """
        return Task(
            description=f"Store transcription for file {file_id} in local storage",
            agent=self.agent,
            expected_output="Storage confirmation and file path"
        )
