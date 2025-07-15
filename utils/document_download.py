"""
Document Download utility for the CrewAI Multi-Agent Project Documentation System.
This module provides functionality to download documentation in various formats.
"""
import os
import json
import shutil
from typing import Dict, Any, Optional
from fastapi import HTTPException
from fastapi.responses import FileResponse

from utils.logger import get_agent_logger

# Setup logger
logger = get_agent_logger("document_download")

async def get_document_for_download(file_id: str, format_type: str = "json") -> FileResponse:
    """
    Get a document for download in the specified format.
    
    Args:
        file_id: Unique identifier for the file
        format_type: Format type for download (json, pdf, docx, html)
        
    Returns:
        FileResponse: File response for download
    """
    try:
        # Check if format type is supported
        if format_type.lower() not in ["json", "pdf", "docx", "html"]:
            raise HTTPException(status_code=400, detail=f"Unsupported format type: {format_type}")
            
        # Get document path based on format type
        if format_type.lower() == "json":
            doc_path = os.path.join("data", "documentations", f"{file_id}.json")
            media_type = "application/json"
            filename = f"documentation_{file_id}.json"
        elif format_type.lower() == "pdf":
            doc_path = os.path.join("data", "pdf_documentations", f"{file_id}.pdf")
            media_type = "application/pdf"
            filename = f"documentation_{file_id}.pdf"
        elif format_type.lower() == "docx":
            doc_path = os.path.join("data", "docx_documentations", f"{file_id}.docx")
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"documentation_{file_id}.docx"
        elif format_type.lower() == "html":
            doc_path = os.path.join("data", "html_documentations", f"{file_id}.html")
            media_type = "text/html"
            filename = f"documentation_{file_id}.html"
            
        # Check if document exists
        if not os.path.exists(doc_path):
            logger.error(f"Document not found: {doc_path}")
            
            # If a specific format is requested but doesn't exist, check if JSON exists and try to generate it
            json_path = os.path.join("data", "documentations", f"{file_id}.json")
            if os.path.exists(json_path):
                # Initialize the appropriate document generator based on format
                if format_type.lower() == "pdf":
                    from utils.pdf_generator import generate_pdf_from_json
                    generated_path = generate_pdf_from_json(json_path)
                elif format_type.lower() in ["docx", "html"]:
                    # For docx and html, we need to use the DocumentGenerator service
                    from services.document_generator import DocumentGenerator
                    doc_generator = DocumentGenerator()
                    
                    # Load the JSON document
                    with open(json_path, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                    
                    # Generate the document
                    import asyncio
                    if format_type.lower() == "docx":
                        result = asyncio.run(doc_generator.generate_docx(doc_data))
                        generated_path = result.get("file_path") if result.get("success") else None
                    else:  # HTML
                        result = asyncio.run(doc_generator.generate_html(doc_data))
                        generated_path = result.get("file_path") if result.get("success") else None
                else:
                    generated_path = None
                    
                # Return the generated document if available
                if generated_path and os.path.exists(generated_path):
                    logger.info(f"Generated {format_type.upper()} on demand: {generated_path}")
                    return FileResponse(
                        path=generated_path,
                        media_type=media_type,
                        filename=filename
                    )
            
            raise HTTPException(status_code=404, detail=f"Document not found for file_id: {file_id}")
            
        # Return file response
        logger.info(f"Returning document for download: {doc_path}")
        return FileResponse(
            path=doc_path,
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        logger.error(f"Error getting document for download: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting document for download: {str(e)}")
