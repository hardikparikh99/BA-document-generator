"""
Document Download Agent for the CrewAI Multi-Agent Project Documentation System.
This agent handles document export and download management.
"""
import os
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime, timedelta

from crewai import Agent, Task
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from utils.config import get_settings, get_temp_dir
from utils.logger import get_agent_logger
from services.document_generator import DocumentGenerator
from models.database import get_documentation, get_download_info, store_download_info

# Setup logger
logger = get_agent_logger("download")
settings = get_settings()

class PDFGeneratorTool(BaseTool):
    """Tool for generating PDF documents."""
    
    name: str = "pdf_generator_tool"
    description: str = "Generates PDF documents from documentation"
    
    def __init__(self):
        """Initialize the PDF generator tool."""
        super().__init__()
        self.document_generator = DocumentGenerator()
    
    async def _arun(self, documentation_id: str) -> Dict[str, Any]:
        """
        Generate a PDF document.
        
        Args:
            documentation_id: ID of the documentation to generate
            
        Returns:
            dict: Result of the operation with file_path and download_url
        """
        return await self.document_generator.generate_document(documentation_id, "pdf")
    
    def _run(self, documentation_id: str) -> Dict[str, Any]:
        """Synchronous run method (required by BaseTool)."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(documentation_id))

class DOCXGeneratorTool(BaseTool):
    """Tool for generating DOCX documents."""
    
    name: str = "docx_generator_tool"
    description: str = "Generates DOCX documents from documentation"
    
    def __init__(self):
        """Initialize the DOCX generator tool."""
        super().__init__()
        self.document_generator = DocumentGenerator()
    
    async def _arun(self, documentation_id: str) -> Dict[str, Any]:
        """
        Generate a DOCX document.
        
        Args:
            documentation_id: ID of the documentation to generate
            
        Returns:
            dict: Result of the operation with file_path and download_url
        """
        return await self.document_generator.generate_document(documentation_id, "docx")
    
    def _run(self, documentation_id: str) -> Dict[str, Any]:
        """Synchronous run method (required by BaseTool)."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(documentation_id))

class HTMLGeneratorTool(BaseTool):
    """Tool for generating HTML documents."""
    
    name: str = "html_generator_tool"
    description: str = "Generates HTML documents from documentation"
    
    def __init__(self):
        """Initialize the HTML generator tool."""
        super().__init__()
        self.document_generator = DocumentGenerator()
    
    async def _arun(self, documentation_id: str) -> Dict[str, Any]:
        """
        Generate an HTML document.
        
        Args:
            documentation_id: ID of the documentation to generate
            
        Returns:
            dict: Result of the operation with file_path and download_url
        """
        return await self.document_generator.generate_document(documentation_id, "html")
    
    def _run(self, documentation_id: str) -> Dict[str, Any]:
        """Synchronous run method (required by BaseTool)."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(documentation_id))

class FileCleanupTool(BaseTool):
    """Tool for cleaning up temporary files."""
    
    name: str = "file_cleanup_tool"
    description: str = "Cleans up temporary files after download"
    
    def __init__(self):
        """Initialize the file cleanup tool."""
        super().__init__()
        self.temp_dir = get_temp_dir()
    
    async def _arun(self, file_path: str, delay_hours: int = 24) -> Dict[str, Any]:
        """
        Schedule cleanup of a file after a delay.
        
        Args:
            file_path: Path to the file to clean up
            delay_hours: Number of hours to wait before cleanup
            
        Returns:
            dict: Result of the operation
        """
        try:
            # Schedule cleanup
            asyncio.create_task(self._delayed_cleanup(file_path, delay_hours))
            
            return {
                "success": True,
                "message": f"Cleanup scheduled for {file_path} in {delay_hours} hours"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error scheduling cleanup: {str(e)}"
            }
    
    async def _delayed_cleanup(self, file_path: str, delay_hours: int):
        """
        Clean up a file after a delay.
        
        Args:
            file_path: Path to the file to clean up
            delay_hours: Number of hours to wait before cleanup
        """
        try:
            # Wait for the specified delay
            await asyncio.sleep(delay_hours * 3600)
            
            # Check if file exists and remove it
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {str(e)}")
    
    def _run(self, file_path: str, delay_hours: int = 24) -> Dict[str, Any]:
        """Synchronous run method (required by BaseTool)."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(file_path, delay_hours))

class DownloadAgent:
    """
    Agent responsible for document export and download management.
    """
    
    def __init__(self):
        """Initialize the Document Download Agent."""
        self.logger = logger
        self.document_generator = DocumentGenerator()
        
        # Create tools
        self.pdf_generator_tool = PDFGeneratorTool()
        self.docx_generator_tool = DOCXGeneratorTool()
        self.html_generator_tool = HTMLGeneratorTool()
        self.file_cleanup_tool = FileCleanupTool()
        
        # Create CrewAI agent
        self.agent = Agent(
            role="Document Export Manager",
            goal="Generate and manage document downloads",
            backstory="Expert in document generation and file management",
            verbose=True,
            tools=[]
        )
        
        # Add tools to agent after initialization
        self.agent.tools = [
            self.pdf_generator_tool, 
            self.docx_generator_tool, 
            self.html_generator_tool,
            self.file_cleanup_tool
        ]
    
    async def prepare_download(self, file_id: str, format: str = "pdf") -> Dict[str, Any]:
        """
        Prepare a document for download.
        
        Args:
            file_id: Unique identifier for the file
            format: Document format (pdf, docx, html)
            
        Returns:
            dict: Result of the operation with download_url
        """
        try:
            # Check if download already exists
            existing_download = await get_download_info(file_id, format)
            if existing_download:
                # Check if the file still exists
                if os.path.exists(existing_download["file_path"]):
                    self.logger.info(f"Using existing download for file {file_id} in format {format}")
                    return {
                        "success": True,
                        "documentation_id": existing_download["documentation_id"],
                        "download_url": existing_download["download_url"]
                    }
            
            # Get documentation
            documentation = await get_documentation(file_id)
            if not documentation:
                self.logger.error(f"Documentation not found for file: {file_id}")
                return {
                    "success": False,
                    "message": "Documentation not found"
                }
            
            # Generate document
            result = await self.document_generator.generate_document(
                documentation["documentation_id"], 
                format
            )
            
            if result["success"]:
                self.logger.info(f"Document generated successfully for file {file_id} in format {format}")
                
                # Schedule cleanup
                await self.file_cleanup_tool._arun(result["file_path"], 24)
                
                return {
                    "success": True,
                    "documentation_id": documentation["documentation_id"],
                    "download_url": result["download_url"]
                }
            else:
                self.logger.error(f"Document generation failed: {result.get('message', 'Unknown error')}")
                return {
                    "success": False,
                    "message": result.get("message", "Unknown error")
                }
            
        except Exception as e:
            self.logger.error(f"Error in prepare_download: {str(e)}")
            return {
                "success": False,
                "message": f"Error preparing download: {str(e)}"
            }
    
    def create_task(self, file_id: str, format: str = "pdf") -> Task:
        """
        Create a CrewAI task for document export.
        
        Args:
            file_id: Unique identifier for the file
            format: Document format (pdf, docx, html)
            
        Returns:
            Task: CrewAI task
        """
        return Task(
            description=f"Generate {format.upper()} document for file {file_id}",
            agent=self.agent,
            expected_output="Download link and file management"
        )
