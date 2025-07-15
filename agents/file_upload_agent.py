"""
File Upload Handler Agent for the CrewAI Multi-Agent Project Documentation System.
This agent handles file reception, validation, and initial processing.
"""
import os
import uuid
from typing import Dict, Any, Optional, List
from fastapi import UploadFile
import aiofiles
import asyncio

from crewai import Agent, Task
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from utils.config import get_settings
from utils.logger import get_agent_logger
from utils.file_handler import (
    is_valid_file_type, 
    is_valid_file_size, 
    generate_file_id, 
    get_file_path,
    save_uploaded_file
)
from models.database import store_file_metadata, update_processing_status

# Setup logger
logger = get_agent_logger("file_upload")
settings = get_settings()

class FileValidationTool(BaseTool):
    """Tool for validating uploaded files."""
    
    name: str = "file_validation_tool"
    description: str = "Validates file format and size"
    
    async def _arun(self, file_id: str, file_path: str) -> Dict[str, Any]:
        """
        Validate a file.
        
        Args:
            file_id: Unique identifier for the file
            file_path: Path to the file
            
        Returns:
            dict: Validation result
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {
                    "valid": False,
                    "message": "File not found"
                }
            
            # Check file type
            if not is_valid_file_type(file_path):
                return {
                    "valid": False,
                    "message": "Invalid file type"
                }
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if not is_valid_file_size(file_size):
                return {
                    "valid": False,
                    "message": f"File too large. Maximum size: {settings.max_file_size}"
                }
            
            # File is valid
            return {
                "valid": True,
                "file_id": file_id,
                "file_path": file_path,
                "file_size": file_size
            }
            
        except Exception as e:
            logger.error(f"Error validating file: {str(e)}")
            return {
                "valid": False,
                "message": f"Error validating file: {str(e)}"
            }
    
    def _run(self, file_id: str, file_path: str) -> Dict[str, Any]:
        """Synchronous run method (required by BaseTool)."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(file_id, file_path))

class UUIDGeneratorTool(BaseTool):
    """Tool for generating unique file IDs."""
    
    name: str = "uuid_generator_tool"
    description: str = "Generates a unique file ID"
    
    def _run(self) -> str:
        """
        Generate a unique file ID.
        
        Returns:
            str: Unique file ID
        """
        return str(uuid.uuid4())
    
    async def _arun(self) -> str:
        """Asynchronous run method."""
        return self._run()

class FileUploadAgent:
    """
    Agent responsible for handling file uploads, validation, and initial processing.
    """
    
    def __init__(self):
        """Initialize the File Upload Handler Agent."""
        self.logger = logger
        
        # Create tools
        self.file_validation_tool = FileValidationTool()
        self.uuid_generator_tool = UUIDGeneratorTool()
        
        # Create CrewAI agent
        self.agent = Agent(
            role="File Upload Handler",
            goal="Process and validate uploaded media files",
            backstory="Expert in file handling and validation",
            verbose=True,
            tools=[]
        )
        
        # Add tools to agent after initialization
        self.agent.tools = [self.file_validation_tool, self.uuid_generator_tool]
    
    async def save_file(self, upload_file: UploadFile) -> Dict[str, Any]:
        """
        Save an uploaded file and generate a file ID.
        
        Args:
            upload_file: The uploaded file
            
        Returns:
            dict: Result of the operation with file_id and file_path
        """
        try:
            # Save the uploaded file
            result = await save_uploaded_file(upload_file)
            
            if result["success"]:
                # Store file metadata
                metadata = {
                    "file_id": result["file_id"],
                    "original_filename": result["original_filename"],
                    "file_size": result["file_size"],
                    "file_type": os.path.splitext(upload_file.filename)[1][1:],  # Remove the dot
                }
                
                await store_file_metadata(metadata)
                
                # Update processing status
                await update_processing_status(
                    file_id=result["file_id"],
                    status="uploaded",
                    progress=10,
                    current_stage="upload"
                )
                
                self.logger.info(f"File uploaded successfully: {result['file_id']}")
            else:
                self.logger.error(f"Error saving file: {result['message']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in save_file: {str(e)}")
            return {
                "success": False,
                "message": f"Error saving file: {str(e)}"
            }
    
    async def validate_file(self, file_id: str, file_path: str) -> Dict[str, Any]:
        """
        Validate a file.
        
        Args:
            file_id: Unique identifier for the file
            file_path: Path to the file
            
        Returns:
            dict: Validation result
        """
        try:
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="processing",
                progress=20,
                current_stage="validation"
            )
            
            # Validate file
            result = await self.file_validation_tool._arun(file_id, file_path)
            
            if result["valid"]:
                self.logger.info(f"File validated successfully: {file_id}")
            else:
                self.logger.error(f"File validation failed: {result['message']}")
                
                # Update processing status
                await update_processing_status(
                    file_id=file_id,
                    status="failed",
                    progress=0,
                    current_stage="validation",
                    error=result["message"]
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in validate_file: {str(e)}")
            
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="failed",
                progress=0,
                current_stage="validation",
                error=str(e)
            )
            
            return {
                "valid": False,
                "message": f"Error validating file: {str(e)}"
            }
    
    def create_task(self, file_id: str, file_path: str) -> Task:
        """
        Create a CrewAI task for file validation.
        
        Args:
            file_id: Unique identifier for the file
            file_path: Path to the file
            
        Returns:
            Task: CrewAI task
        """
        return Task(
            description=f"Validate file {file_id} at {file_path}",
            agent=self.agent,
            expected_output="Validation result with file ID and status"
        )
