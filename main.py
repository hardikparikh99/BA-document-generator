"""
FastAPI entry point for the CrewAI Multi-Agent Project Documentation System.
This module sets up the FastAPI application and defines the API endpoints.
"""
import os
import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
from datetime import datetime
import uvicorn

from utils.config import get_settings
from utils.logger import setup_logger
from services.llm_service import LLMService
from agents.file_upload_agent import FileUploadAgent
from agents.media_processing_agent import MediaProcessingAgent
from agents.vector_storage_agent import VectorStorageAgent
from agents.documentation_agent import DocumentationAgent
from agents.sow_agent import SOWAgent
from agents.frd_agent import FRDAgent
from services.local_storage_service import LocalStorageService
from agents.download_agent import DownloadAgent
from models.database import (update_processing_status, get_processing_status, 
                           get_file_metadata, store_file_metadata)
from utils.document_download import get_document_for_download

# Setup logging
logger = setup_logger()
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="Business Analyst Documentation Generator",
    description="A multi-agent system that processes media files and generates project documentation",
    version="1.0.0"
)

# Set up templates
templates = Jinja2Templates(directory="templates")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create static/downloads directory if it doesn't exist
os.makedirs("static/downloads", exist_ok=True)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response models
class ProcessingResponse(BaseModel):
    file_id: str
    status: str
    message: str

class DocumentationResponse(BaseModel):
    file_id: str
    documentation_id: str
    status: str

class DownloadResponse(BaseModel):
    file_id: str
    documentation_id: str
    download_url: str
    format: str

class DocumentType(str, Enum):
    """Document types supported by the system"""
    BRD = "BRD"
    SOW = "SOW"
    FRD = "FRD"

# Background task to process media file
async def process_media_file(file_id: str, file_path: str, doc_type: str = "BRD", doc_level: str = "Intermediate"):
    """
    Background task to process media file through the agent workflow.
    
    Args:
        file_id: Unique identifier for the file
        file_path: Path to the uploaded file
        doc_type: Type of document to generate (BRD, SOW, or FRD)
        doc_level: Level of documentation detail (Simple, Intermediate, or Advanced)
    """
    try:
        logger.info(f"Starting processing for file_id: {file_id}, doc_type: {doc_type}")
        
        # Initialize agents
        file_upload_agent = FileUploadAgent()
        media_processing_agent = MediaProcessingAgent()
        vector_storage_agent = VectorStorageAgent()
        
        # Select documentation agent based on document type
        if doc_type == "BRD":
            documentation_agent = DocumentationAgent()
        elif doc_type == "SOW":
            documentation_agent = SOWAgent()
        elif doc_type == "FRD":
            documentation_agent = FRDAgent()
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")
        
        # Update status to processing
        await update_processing_status(
            file_id=file_id,
            status="processing",
            progress=10,
            current_stage="validation",
            error=None
        )
        
        # Process file through agents - Validation stage
        validation_result = await file_upload_agent.validate_file(file_id, file_path)
        if not validation_result["valid"]:
            error_msg = validation_result.get('message', 'File validation failed')
            logger.error(f"File validation failed: {error_msg}")
            
            # Update status to failed
            await update_processing_status(
                file_id=file_id,
                status="failed",
                progress=10,
                current_stage="validation",
                error=error_msg
            )
            return
        
        # Update status to transcription stage
        await update_processing_status(
            file_id=file_id,
            status="processing",
            progress=25,
            current_stage="transcription",
            error=None
        )
        
        # Transcription stage
        transcription_result = await media_processing_agent.process_file(file_id, file_path)
        if not transcription_result["success"]:
            error_msg = transcription_result.get('message', 'Transcription failed')
            logger.error(f"Transcription failed: {error_msg}")
            
            # Update status to failed
            await update_processing_status(
                file_id=file_id,
                status="failed",
                progress=25,
                current_stage="transcription",
                error=error_msg
            )
            return
        
        # Update status to vector storage stage
        await update_processing_status(
            file_id=file_id,
            status="processing",
            progress=50,
            current_stage="vector_storage",
            error=None
        )
        
        # Vector storage stage
        storage_result = await vector_storage_agent.store_transcription(
            file_id, 
            transcription_result["transcription"], 
            transcription_result["metadata"]
        )
        if not storage_result["success"]:
            error_msg = storage_result.get('message', 'Vector storage failed')
            logger.error(f"Vector storage failed: {error_msg}")
            
            # Update status to failed
            await update_processing_status(
                file_id=file_id,
                status="failed",
                progress=50,
                current_stage="vector_storage",
                error=error_msg
            )
            return
        
        # Update status to documentation generation stage
        await update_processing_status(
            file_id=file_id,
            status="processing",
            progress=75,
            current_stage="documentation",
            error=None
        )
        
        # Documentation generation stage
        logger.info(f"Starting {doc_type} generation for file: {file_id}")
        
        # Get the transcription data to pass to documentation agent
        storage_service = LocalStorageService()
        transcription_data = await storage_service.retrieve_transcription(file_id)
        
        if not transcription_data:
            error_msg = "Failed to retrieve transcription for documentation generation"
            logger.error(error_msg)
            await update_processing_status(
                file_id=file_id,
                status="failed",
                progress=75,
                current_stage="documentation",
                error=error_msg
            )
            return
            
        # Generate documentation
        documentation_result = await documentation_agent.generate_documentation(file_id, doc_level)
        
        if not documentation_result.get("success", False):
            error_msg = documentation_result.get('message', 'Documentation generation failed')
            logger.error(f"Documentation generation failed: {error_msg}")
            
            # Update status to failed
            await update_processing_status(
                file_id=file_id,
                status="failed",
                progress=75,
                current_stage="documentation",
                error=error_msg
            )
            return
        
        # Update status to completed
        await update_processing_status(
            file_id=file_id,
            status="completed",
            progress=100,
            current_stage="completed",
            error=None
        )
        
        logger.info(f"Processing completed for file_id: {file_id}")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error processing file {file_id}: {error_msg}")
        
        # Update status to failed
        await update_processing_status(
            file_id=file_id,
            status="failed",
            progress=0,
            current_stage="error",
            error=error_msg
        )

@app.get("/")
async def root():
    """Root endpoint to check if the API is running."""
    return {"message": "Business Analyst Documentation Generator API is running"}

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    doc_type: DocumentType = Form(DocumentType.BRD),
    doc_level: str = Form("Intermediate")
):
    """
    Upload a media file for processing and documentation generation.
    
    Args:
        file: The media file to upload
        doc_type: Type of document to generate (BRD, SOW, or FRD)
        doc_level: Level of documentation detail (Simple, Intermediate, or Advanced)
    """
    try:
        # Initialize agents
        file_upload_agent = FileUploadAgent()
        media_processing_agent = MediaProcessingAgent()
        vector_storage_agent = VectorStorageAgent()
        
        # Step 1: Save uploaded file
        logger.info(f"Saving uploaded file: {file.filename}")
        file_result = await file_upload_agent.save_file(file)
        
        if not file_result["success"]:
            raise HTTPException(status_code=400, detail=file_result["message"])
        
        file_id = file_result["file_id"]
        file_path = file_result["file_path"]
        
        # Step 2: Validate file
        logger.info(f"Validating file: {file_id}")
        validation_result = await file_upload_agent.validate_file(file_id, file_path)
        
        if not validation_result["valid"]:
            error_msg = validation_result.get('message', 'File validation failed')
            logger.error(f"File validation failed: {error_msg}")
            return {
                "success": False,
                "stage": "validation",
                "message": error_msg
            }
        
        # Step 3: Process file (extract audio and transcribe)
        logger.info(f"Processing file: {file_id}")
        transcription_result = await media_processing_agent.process_file(file_id, file_path)
        
        if not transcription_result["success"]:
            error_msg = transcription_result.get('message', 'Transcription failed')
            logger.error(f"Transcription failed: {error_msg}")
            return {
                "success": False,
                "stage": "transcription",
                "message": error_msg
            }
        
        # Step 4: Store transcription in vector storage
        logger.info(f"Storing transcription in vector storage: {file_id}")
        storage_result = await vector_storage_agent.store_transcription(
            file_id, 
            transcription_result["transcription"], 
            transcription_result["metadata"]
        )
        
        if not storage_result["success"]:
            error_msg = storage_result.get('message', 'Vector storage failed')
            logger.error(f"Vector storage failed: {error_msg}")
            return {
                "success": False,
                "stage": "vector_storage",
                "message": error_msg
            }

        # Step 5: Generate documentation using appropriate agent
        logger.info(f"Generating {doc_type} documentation for file: {file_id}")
        
        # Select documentation agent based on document type
        if doc_type == "BRD":
            documentation_agent = DocumentationAgent()
        elif doc_type == "SOW":
            documentation_agent = SOWAgent()
        elif doc_type == "FRD":
            documentation_agent = FRDAgent()
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")
        
        # Generate documentation
        documentation_result = await documentation_agent.generate_documentation(file_id, doc_level)
        
        if not documentation_result.get("success", False):
            error_msg = documentation_result.get('message', 'Documentation generation failed')
            logger.error(f"Documentation generation failed: {error_msg}")
            return {
                "success": False,
                "stage": "documentation",
                "message": error_msg
            }

        logger.info(f"Processing completed successfully for file: {file_id}")
        return {
            "success": True,
            "file_id": file_id,
            "documentation_id": documentation_result.get("documentation_id"),
            "transcription_length": len(transcription_result["transcription"]),
            "message": f"File processed successfully, {doc_type} documentation generated"
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in upload_file: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/documentation/{file_id}")
async def get_documentation(file_id: str):
    """
    Get the generated documentation for a file.
    
    Args:
        file_id: Unique identifier for the file
        
    Returns:
        dict: Documentation data
    """
    try:
        # Initialize documentation agent
        documentation_agent = DocumentationAgent()
        
        # Get documentation
        documentation = await documentation_agent.get_documentation(file_id)
        
        if not documentation:
            raise HTTPException(status_code=404, detail="Documentation not found")
            
        return documentation
    except Exception as e:
        logger.error(f"Error in get_documentation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

from enum import Enum
from fastapi import Query

class DownloadFormat(str, Enum):
    pdf = "pdf"
    docx = "docx"
    html = "html"
    json = "json"

@app.get("/status/{file_id}")
async def get_status(file_id: str):
    """
    Get the processing status for a file.
    
    Args:
        file_id: Unique identifier for the file
        
    Returns:
        dict: Status information including progress, current stage, etc.
    """
    try:
        status = await get_processing_status(file_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Status not found")
        return status
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in get_status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{file_id}")
async def download_document(
    file_id: str,
    format: DownloadFormat = Query(
        DownloadFormat.pdf,
        description="Document format to download",
        title="Format",
    ),
):
    """
    Download a document in the selected format.
    Args:
        file_id: Unique identifier for the file
        format: Document format (json, pdf, docx, html)
    Returns:
        FileResponse: The document file for download
    """
    try:
        return await get_document_for_download(file_id, format.value)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in download_document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable auto-reload
        log_level="info"
    )
