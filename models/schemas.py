"""
Pydantic models for the CrewAI Multi-Agent Project Documentation System.
This module defines the data schemas used throughout the application.
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

class FileMetadata(BaseModel):
    """Metadata for an uploaded file."""
    file_id: str
    original_filename: str
    file_size: int
    file_type: str
    upload_time: datetime = Field(default_factory=datetime.now)
    
    @validator('file_id')
    def validate_file_id(cls, v):
        """Validate that file_id is a valid UUID."""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('file_id must be a valid UUID')

class TranscriptionMetadata(BaseModel):
    """Metadata for a transcription."""
    file_id: str
    duration: float
    language: str
    speakers: Optional[int] = None
    file_type: str
    transcription_time: datetime = Field(default_factory=datetime.now)

class VectorMetadata(BaseModel):
    """Metadata for a vector stored in Pinecone."""
    file_id: str
    transcription_id: str
    duration: float
    language: str
    file_type: str
    speakers: Optional[int] = None
    storage_time: datetime = Field(default_factory=datetime.now)

class DocumentationSection(BaseModel):
    """A section of the generated documentation."""
    title: str
    content: str
    order: int

class Documentation(BaseModel):
    """Complete project documentation."""
    documentation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_id: str
    title: str
    executive_summary: str
    project_scope: str
    stakeholder_analysis: str
    functional_requirements: str
    technical_requirements: str
    timeline: str
    budget: str
    risk_assessment: str
    assumptions: str
    next_steps: str
    generation_time: datetime = Field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the documentation to a dictionary."""
        return {
            "documentation_id": self.documentation_id,
            "file_id": self.file_id,
            "title": self.title,
            "executive_summary": self.executive_summary,
            "project_scope": self.project_scope,
            "stakeholder_analysis": self.stakeholder_analysis,
            "functional_requirements": self.functional_requirements,
            "technical_requirements": self.technical_requirements,
            "timeline": self.timeline,
            "budget": self.budget,
            "risk_assessment": self.risk_assessment,
            "assumptions": self.assumptions,
            "next_steps": self.next_steps,
            "generation_time": self.generation_time.isoformat()
        }

class DownloadRequest(BaseModel):
    """Request to download documentation."""
    file_id: str
    format: str = Field(default="pdf")
    
    @validator('format')
    def validate_format(cls, v):
        """Validate that format is one of the supported formats."""
        if v not in ["pdf", "docx", "html"]:
            raise ValueError('format must be one of: pdf, docx, html')
        return v

class DownloadResponse(BaseModel):
    """Response with download information."""
    file_id: str
    documentation_id: str
    download_url: str
    format: str
    expiry_time: datetime

class ProcessingStatus(BaseModel):
    """Status of file processing."""
    file_id: str
    status: str
    progress: int = 0
    current_stage: str
    error: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.now)
    update_time: datetime = Field(default_factory=datetime.now)
    
    @validator('status')
    def validate_status(cls, v):
        """Validate that status is one of the expected values."""
        if v not in ["uploaded", "processing", "completed", "failed"]:
            raise ValueError('status must be one of: uploaded, processing, completed, failed')
        return v
    
    @validator('progress')
    def validate_progress(cls, v):
        """Validate that progress is between 0 and 100."""
        if v < 0 or v > 100:
            raise ValueError('progress must be between 0 and 100')
        return v
