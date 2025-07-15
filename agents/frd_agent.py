"""
Functional Requirements Document (FRD) Generator Agent for the CrewAI Multi-Agent Project Documentation System.
This agent transforms meeting transcriptions into comprehensive Functional Requirements Documents.
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import asyncio
from pathlib import Path
import re
from dataclasses import dataclass, asdict
from enum import Enum

from crewai import Agent, Task
from pydantic import BaseModel, Field, validator

from utils.config import get_settings
from utils.logger import get_agent_logger
from utils.pdf_generator import generate_pdf_from_json
from services.llm_service import LLMService
from services.local_storage_service import LocalStorageService
from models.database import store_documentation, get_documentation, update_processing_status

# Setup logger
logger = get_agent_logger("frd")
settings = get_settings()

# Ensure documentations directory exists
Path("data/documentations").mkdir(parents=True, exist_ok=True)

class DocumentationLevel(Enum):
    """Documentation complexity levels"""
    SIMPLE = "Simple"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"

class ProcessingStatus(Enum):
    """Processing status options"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class DocumentationMetrics:
    """Metrics for documentation quality and processing"""
    word_count: int = 0
    section_count: int = 0
    processing_time: float = 0.0
    quality_score: float = 0.0
    completeness_score: float = 0.0

class FRDConfig:
    """Configuration for FRD generation"""
    
    SYSTEM_PROMPTS = {
        DocumentationLevel.SIMPLE: """You are a Senior Systems Analyst with 10+ years of experience specializing in creating clear, concise Functional Requirements Documents. Your expertise lies in transforming business requirements into detailed functional specifications that developers can implement.

Your approach is:
- Focus on essential functional requirements
- Create clear, actionable specifications
- Maintain professional structure while being concise
- Ensure all critical system elements are covered
- Present information in a straightforward, accessible manner

You excel at identifying key system functions, user interactions, and technical requirements from meeting discussions.""",
        
        DocumentationLevel.INTERMEDIATE: """You are a Distinguished Senior Systems Analyst and Technical Consultant with 15+ years of experience creating comprehensive Functional Requirements Documents for enterprise-level systems. You have successfully delivered FRDs for Fortune 500 companies and high-growth startups across various industries.

Your methodology combines:
- Technical analysis with deep system architecture insight
- Comprehensive requirements gathering and documentation
- System integration planning
- Performance and security requirements
- Implementation strategy development
- Stakeholder management and communication excellence

You are known for creating FRDs that not only define functional requirements but provide technical context, system architecture, and clear implementation guidelines.""",
        
        DocumentationLevel.ADVANCED: """You are a Distinguished Senior Systems Analyst and Technical Consultant with 20+ years of elite experience serving Fortune 100 companies, global financial institutions, and unicorn startups. You are recognized as a thought leader in systems analysis, having authored industry-standard methodologies used worldwide.

Your Functional Requirements Documents are legendary in the industry for their:
- Technical depth and analytical rigor
- Ability to guide complex system implementations
- Comprehensive system architecture planning
- Advanced security and performance requirements
- Sophisticated integration frameworks
- Detailed technical specifications
- Quality assurance and testing frameworks

You have successfully led digital transformations worth over $500M and your FRDs consistently rank above industry standards in quality and technical impact."""
    }
    
    USER_PROMPTS = {
        DocumentationLevel.SIMPLE: """Based on the following meeting transcription, create a comprehensive Functional Requirements Document (FRD) that captures all essential system requirements and specifications.

**Meeting Transcription:**
{transcription}

**Current Date:** {current_date}

**Requirements:**
Create a professional FRD that includes:

1. **System Overview**
   - System purpose and scope
   - Key stakeholders and users
   - System context

2. **Functional Requirements**
   - User roles and permissions
   - Core system functions
   - User interactions

3. **System Features**
   - Feature descriptions
   - User workflows
   - Business rules

4. **Technical Requirements**
   - System architecture
   - Integration points
   - Performance requirements

5. **User Interface**
   - UI/UX requirements
   - Screen layouts
   - Navigation flows

6. **Data Requirements**
   - Data structures
   - Data validation
   - Data storage

7. **Testing Requirements**
   - Test scenarios
   - Acceptance criteria
   - Quality metrics

**Output Requirements:**
- Professional markdown format
- Clear, concise language
- Actionable specifications
- 4-6 pages when converted to PDF
- Focus on essential system elements
- Ensure all critical information from the transcription is captured accurately""",
        
        DocumentationLevel.INTERMEDIATE: """Transform the following meeting transcription into a comprehensive, technical Functional Requirements Document that demonstrates enterprise-level systems analysis excellence and provides detailed implementation guidance.

**Meeting Transcription:**
{transcription}

**Current Date:** {current_date}

**Documentation Requirements:**
Create a professional, technical FRD that includes:

1. **Executive Summary**
   - System context and objectives
   - Technical scope
   - Key stakeholders
   - System architecture overview

2. **System Architecture**
   - Technical architecture
   - System components
   - Integration framework
   - Security architecture

3. **Functional Requirements**
   - User roles and permissions
   - Core system functions
   - Business processes
   - System workflows

4. **Technical Specifications**
   - System requirements
   - Performance criteria
   - Security requirements
   - Integration specifications

5. **User Interface Design**
   - UI/UX requirements
   - Screen specifications
   - Navigation structure
   - User interactions

6. **Data Architecture**
   - Data models
   - Data flows
   - Storage requirements
   - Data security

7. **Integration Requirements**
   - API specifications
   - External systems
   - Data exchange
   - Security protocols

8. **Quality Assurance**
   - Testing strategy
   - Test scenarios
   - Performance testing
   - Security testing

**Output Requirements:**
- Professional markdown format
- Technical depth and clarity
- Comprehensive coverage
- 8-12 pages when converted to PDF
- Include all critical system elements
- Ensure technical feasibility and completeness""",
        
        DocumentationLevel.ADVANCED: """Transform the following meeting transcription into an elite-level Functional Requirements Document that sets new industry standards for technical documentation and system specification.

**Meeting Transcription:**
{transcription}

**Current Date:** {current_date}

**Documentation Requirements:**
Create a world-class, technical FRD that includes:

1. **Strategic System Framework**
   - Enterprise architecture context
   - Technical strategy
   - System vision
   - Innovation framework

2. **Comprehensive System Architecture**
   - Technical architecture
   - System components
   - Integration framework
   - Security architecture
   - Scalability design

3. **Advanced Functional Requirements**
   - User role matrix
   - Function hierarchy
   - Process workflows
   - Business rules engine
   - System interactions

4. **Technical Excellence Framework**
   - Performance architecture
   - Security framework
   - Integration patterns
   - Scalability strategy
   - Reliability design

5. **Enterprise User Experience**
   - UX architecture
   - UI framework
   - Interaction patterns
   - Accessibility standards
   - User journey maps

6. **Advanced Data Architecture**
   - Data models
   - Data flows
   - Storage architecture
   - Data security
   - Data governance

7. **Integration Excellence**
   - API architecture
   - Integration patterns
   - Security protocols
   - Performance standards
   - Monitoring framework

8. **Quality Assurance Framework**
   - Testing strategy
   - Test scenarios
   - Performance testing
   - Security testing
   - Quality metrics

**Output Requirements:**
- Professional markdown format
- Technical depth and clarity
- Comprehensive coverage
- 12-16 pages when converted to PDF
- Include all critical system elements
- Ensure technical excellence and innovation"""
    }

class FRDValidator:
    """Validator for FRD content"""
    
    @staticmethod
    def validate_content(content: str, level: DocumentationLevel) -> Tuple[bool, float, List[str]]:
        """Validate FRD content against required sections and quality standards."""
        required_sections = FRDValidator._get_required_sections(level)
        missing_sections = []
        quality_score = 0.0
        
        # Check for required sections
        for section in required_sections:
            if section.lower() not in content.lower():
                missing_sections.append(section)
            else:
                quality_score += 1.0
        
        # Calculate final quality score
        quality_score = (quality_score / len(required_sections)) * 100
        
        return len(missing_sections) == 0, quality_score, missing_sections
    
    @staticmethod
    def _get_required_sections(level: DocumentationLevel) -> List[str]:
        """Get required sections based on documentation level."""
        base_sections = [
            "System Overview",
            "Functional Requirements",
            "System Features",
            "Technical Requirements",
            "User Interface",
            "Data Requirements",
            "Testing Requirements"
        ]
        
        if level == DocumentationLevel.SIMPLE:
            return base_sections
        elif level == DocumentationLevel.INTERMEDIATE:
            return base_sections + [
                "Executive Summary",
                "System Architecture",
                "Integration Requirements"
            ]
        else:  # Advanced
            return base_sections + [
                "Strategic System Framework",
                "Comprehensive System Architecture",
                "Advanced Functional Requirements",
                "Technical Excellence Framework",
                "Enterprise User Experience",
                "Advanced Data Architecture",
                "Integration Excellence",
                "Quality Assurance Framework"
            ]

class FRDGenerator:
    """Generator for FRD documents"""
    
    def __init__(self):
        """Initialize the FRD generator."""
        self.llm_service = LLMService()
        self.storage_service = LocalStorageService()
        self.validator = FRDValidator()
    
    async def generate_documentation(self, file_id: str, doc_level: str = "Intermediate") -> Dict[str, Any]:
        """
        Generate premium-quality Functional Requirements Document from a meeting transcription.
        
        Args:
            file_id: Unique identifier for the file
            doc_level: Documentation level (Simple, Intermediate, Advanced)
            
        Returns:
            dict: Result of the operation with documentation_id
        """
        start_time = datetime.now()
        
        try:
            # Validate and convert doc_level
            try:
                level = DocumentationLevel(doc_level)
            except ValueError:
                level = DocumentationLevel.INTERMEDIATE
                logger.warning(f"Invalid doc_level '{doc_level}', defaulting to Intermediate")
            
            # Get transcription from local storage
            logger.info(f"Retrieving transcription for file_id: {file_id}")
            transcription_data = await self._get_transcription_with_retry(file_id)
            
            transcription = transcription_data.get("transcription", "")
            metadata = transcription_data.get("metadata", {})
            
            # Validate transcription content
            await self._validate_transcription(transcription)
            
            # Generate documentation with retry mechanism
            documentation_content = await self._generate_content_with_retry(
                transcription, level, file_id
            )
            
            # Validate generated content
            is_valid, quality_score, issues = self.validator.validate_content(
                documentation_content, level
            )
            
            if not is_valid:
                logger.warning(f"Generated content quality issues: {issues}")
                # Optionally retry or enhance content here
            
            # Calculate metrics
            metrics = self._calculate_metrics(documentation_content, start_time)
            metrics.quality_score = quality_score
            
            # Create documentation object
            documentation_id = f"doc_{str(uuid.uuid4())[:8]}"
            documentation = {
                "documentation_id": documentation_id,
                "file_id": file_id,
                "title": f"Functional Requirements Document - {metadata.get('original_filename', 'Untitled')}",
                "content": documentation_content,
                "metadata": {
                    **metadata,
                    "generated_at": datetime.utcnow().isoformat(),
                    "document_type": "functional_requirements_document",
                    "document_version": "1.0",
                    "documentation_level": level.value,
                    "analysis_framework": "Advanced Systems Analysis Methodology",
                    "quality_standard": "Fortune 500 Enterprise Grade",
                    "metrics": asdict(metrics),
                    "validation_issues": issues if issues else None
                }
            }
            
            # Save documentation
            doc_path = await self._save_documentation(documentation, file_id)
            
            # Generate PDF
            pdf_path = await self._generate_pdf_with_retry(doc_path)
            if pdf_path:
                documentation["pdf_path"] = pdf_path
                # Update JSON with PDF path
                await self._update_documentation_file(doc_path, documentation)
            
            # Store in database
            await store_documentation(documentation)
            
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="completed",
                progress=100,
                current_stage="documentation"
            )
            
            logger.info(f"Documentation generated successfully: {documentation_id} (Quality: {quality_score:.1f}%)")
            
            return {
                "success": True,
                "documentation_id": documentation_id,
                "file_path": doc_path,
                "pdf_path": pdf_path,
                "quality_score": quality_score,
                "metrics": asdict(metrics)
            }
            
        except Exception as e:
            error_msg = f"Error generating documentation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="failed",
                progress=0,
                current_stage="documentation",
                error=error_msg
            )
            
            return {
                "success": False,
                "message": error_msg
            }
    
    async def _get_transcription_with_retry(self, file_id: str) -> Dict[str, Any]:
        """Get transcription data with retry mechanism."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return await self.storage_service.retrieve_transcription(file_id)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(1)
    
    async def _validate_transcription(self, transcription: str) -> None:
        """Validate transcription content."""
        if not transcription or len(transcription.strip()) < 100:
            raise Exception("Invalid or insufficient transcription content")
    
    async def _generate_content_with_retry(self, transcription: str, level: DocumentationLevel, file_id: str) -> str:
        """Generate content with retry logic."""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Get the appropriate prompts for the documentation level
                system_prompt = FRDConfig.SYSTEM_PROMPTS[level]
                user_prompt = FRDConfig.USER_PROMPTS[level].format(
                    transcription=transcription,
                    current_date=datetime.now().strftime("%Y-%m-%d")
                )
                
                # Generate content using LLM service
                content = await self.llm_service.generate_response(
                    prompt=user_prompt,
                    system_prompt=system_prompt
                )
                
                # Validate the generated content
                is_valid, quality_score, issues = FRDValidator.validate_content(content, level)
                if is_valid:
                    return content
                
                logger.warning(f"Content validation failed (attempt {attempt + 1}/{max_retries}): {issues}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                
                raise ValueError(f"Failed to generate valid content after {max_retries} attempts")
                
            except Exception as e:
                logger.error(f"Error generating content (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                raise
    
    def _calculate_metrics(self, content: str, start_time: datetime) -> DocumentationMetrics:
        """Calculate documentation metrics."""
        word_count = len(content.split())
        section_count = len(re.findall(r'^#+\s+.+$', content, re.MULTILINE))
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return DocumentationMetrics(
            word_count=word_count,
            section_count=section_count,
            processing_time=processing_time,
            quality_score=100.0,  # Default to 100 if validation passed
            completeness_score=100.0  # Default to 100 if validation passed
        )
    
    async def _save_documentation(self, documentation: Dict[str, Any], file_id: str) -> str:
        """Save documentation to local storage."""
        try:
            # Get metrics from metadata
            metrics = documentation["metadata"]["metrics"]
            
            # Create documentation object for database
            doc_data = {
                "documentation_id": documentation["documentation_id"],
                "file_id": file_id,
                "title": documentation["title"],
                "content": documentation["content"],
                "document_type": documentation["metadata"]["document_type"],
                "documentation_level": documentation["metadata"]["documentation_level"],
                "generated_at": documentation["metadata"]["generated_at"],
                "metrics": metrics
            }
            
            # Store in database
            await store_documentation(doc_data)
            
            # Save to file
            doc_path = os.path.join("data", "documentations", f"{file_id}.json")
            os.makedirs(os.path.dirname(doc_path), exist_ok=True)
            
            with open(doc_path, "w", encoding="utf-8") as f:
                json.dump(documentation, f, indent=2)
            
            logger.info(f"Documentation saved successfully: {doc_path}")
            return doc_path
            
        except Exception as e:
            logger.error(f"Error saving documentation: {str(e)}")
            raise
    
    async def _generate_pdf_with_retry(self, doc_path: str) -> Optional[str]:
        """Generate PDF with retry mechanism."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return await generate_pdf_from_json(doc_path)
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to generate PDF: {str(e)}")
                    return None
                await asyncio.sleep(1)

class FRDAgent:
    """Agent for generating FRD documents"""
    
    def __init__(self):
        """Initialize the FRD agent."""
        self.generator = FRDGenerator()
    
    async def generate_documentation(self, file_id: str, doc_level: str = "Intermediate") -> Dict[str, Any]:
        """Generate FRD documentation."""
        try:
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="processing",
                progress=75,
                current_stage="frd_generation",
                error=None
            )
            
            # Generate documentation
            result = await self.generator.generate_documentation(file_id, doc_level)
            
            if result["success"]:
                # Update processing status
                await update_processing_status(
                    file_id=file_id,
                    status="completed",
                    progress=100,
                    current_stage="completed",
                    error=None
                )
            else:
                # Update processing status
                await update_processing_status(
                    file_id=file_id,
                    status="failed",
                    progress=75,
                    current_stage="frd_generation",
                    error=result["message"]
                )
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in FRD agent: {error_msg}")
            
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="failed",
                progress=75,
                current_stage="frd_generation",
                error=error_msg
            )
            
            return {
                "success": False,
                "message": f"Failed to generate FRD: {error_msg}"
            }
    
    async def get_documentation(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get generated FRD documentation."""
        try:
            return await self.generator.get_documentation(file_id)
        except Exception as e:
            logger.error(f"Error retrieving FRD: {str(e)}")
            return None
    
    async def get_documentation_with_metrics(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get FRD documentation with metrics."""
        try:
            return await self.generator.get_documentation_metrics(file_id)
        except Exception as e:
            logger.error(f"Error retrieving FRD metrics: {str(e)}")
            return None
    
    async def validate_documentation(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Validate generated FRD documentation."""
        try:
            doc = await self.get_documentation(file_id)
            if not doc:
                return None
            
            level = DocumentationLevel(doc.get("level", "Intermediate"))
            is_valid, quality_score, missing_sections = FRDValidator.validate_content(
                doc.get("content", ""),
                level
            )
            
            return {
                "is_valid": is_valid,
                "quality_score": quality_score,
                "missing_sections": missing_sections
            }
            
        except Exception as e:
            logger.error(f"Error validating FRD: {str(e)}")
            return None 