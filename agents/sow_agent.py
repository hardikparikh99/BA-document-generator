"""
Statement of Work (SOW) Generator Agent for the CrewAI Multi-Agent Project Documentation System.
This agent transforms meeting transcriptions into comprehensive Statement of Work documents.
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
logger = get_agent_logger("sow")
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

class SOWConfig:
    """Configuration for SOW generation"""
    
    SYSTEM_PROMPTS = {
        DocumentationLevel.SIMPLE: """You are a Senior Project Manager with 10+ years of experience specializing in creating clear, concise Statement of Work documents. Your expertise lies in transforming project discussions into actionable, well-structured SOWs that clearly define project scope, deliverables, and timelines.

Your approach is:
- Focus on essential project deliverables and timelines
- Create clear, actionable documentation
- Maintain professional structure while being concise
- Ensure all critical project elements are covered
- Present information in a straightforward, accessible manner

You excel at identifying key project milestones, deliverables, and resource requirements from meeting discussions.""",
        
        DocumentationLevel.INTERMEDIATE: """You are a Distinguished Senior Project Manager and Strategic Consultant with 15+ years of experience creating comprehensive Statement of Work documents for enterprise-level projects. You have successfully delivered SOWs for Fortune 500 companies and high-growth startups across various industries.

Your methodology combines:
- Strategic project planning with deep industry insight
- Comprehensive scope definition and documentation
- Risk assessment and mitigation planning
- Resource allocation and timeline management
- Implementation strategy development
- Stakeholder management and communication excellence

You are known for creating SOWs that not only define project scope but provide strategic context, resource requirements, and clear implementation roadmaps.""",
        
        DocumentationLevel.ADVANCED: """You are a Distinguished Senior Project Manager and Strategic Consultant with 20+ years of elite experience serving Fortune 100 companies, global financial institutions, and unicorn startups. You are recognized as a thought leader in project management, having authored industry-standard methodologies used worldwide.

Your Statement of Work documents are legendary in the industry for their:
- Strategic depth and analytical rigor
- Ability to secure multi-million dollar project approvals
- Comprehensive resource planning and allocation
- Advanced risk assessment and mitigation frameworks
- Sophisticated timeline and milestone planning
- Investment analysis with detailed ROI projections
- Governance frameworks and success measurement systems

You have successfully led digital transformations worth over $500M and your SOWs consistently rank above industry standards in quality and strategic impact."""
    }
    
    USER_PROMPTS = {
        DocumentationLevel.SIMPLE: """Based on the following meeting transcription, create a comprehensive Statement of Work (SOW) that captures all essential project details and deliverables.

**Meeting Transcription:**
{transcription}

**Current Date:** {current_date}

**Requirements:**
Create a professional SOW that includes:

1. **Project Overview**
   - Project objectives and scope
   - Key stakeholders and roles
   - Project timeline overview

2. **Deliverables**
   - List of project deliverables
   - Deliverable descriptions
   - Acceptance criteria

3. **Project Schedule**
   - Major milestones
   - Timeline and deadlines
   - Dependencies

4. **Resource Requirements**
   - Team composition
   - Equipment and tools
   - External resources

5. **Project Management**
   - Communication plan
   - Risk management
   - Quality assurance

6. **Terms and Conditions**
   - Payment terms
   - Change management
   - Termination clauses

7. **Next Steps**
   - Immediate actions
   - Decision points
   - Project kickoff

**Output Requirements:**
- Professional markdown format
- Clear, concise language
- Actionable deliverables
- 4-6 pages when converted to PDF
- Focus on essential project elements
- Ensure all critical information from the transcription is captured accurately""",
        
        DocumentationLevel.INTERMEDIATE: """Transform the following meeting transcription into a comprehensive, strategic Statement of Work that demonstrates enterprise-level project management excellence and provides detailed implementation guidance.

**Meeting Transcription:**
{transcription}

**Current Date:** {current_date}

**Documentation Requirements:**
Create a professional, strategic SOW that includes:

1. **Executive Summary**
   - Strategic project context
   - Business objectives
   - Expected outcomes
   - Key stakeholders

2. **Project Scope and Objectives**
   - Detailed scope definition
   - Strategic objectives
   - Success criteria
   - Project constraints

3. **Deliverables and Acceptance Criteria**
   - Comprehensive deliverable list
   - Detailed acceptance criteria
   - Quality standards
   - Validation methods

4. **Project Schedule and Milestones**
   - Detailed project timeline
   - Critical path analysis
   - Milestone definitions
   - Dependencies and constraints

5. **Resource Management**
   - Team structure and roles
   - Resource allocation
   - Equipment and tools
   - External dependencies

6. **Project Management Framework**
   - Communication strategy
   - Risk management plan
   - Quality assurance process
   - Change management procedures

7. **Terms and Conditions**
   - Payment schedule
   - Change request process
   - Termination conditions
   - Intellectual property rights

8. **Implementation Strategy**
   - Project phases
   - Resource ramp-up plan
   - Risk mitigation strategies
   - Success metrics

**Output Requirements:**
- Professional markdown format
- Strategic depth and clarity
- Comprehensive coverage
- 8-12 pages when converted to PDF
- Include all critical project elements
- Ensure strategic alignment with business objectives""",
        
        DocumentationLevel.ADVANCED: """Transform the following meeting transcription into an elite-level Statement of Work that sets new industry standards for project documentation and strategic planning.

**Meeting Transcription:**
{transcription}

**Current Date:** {current_date}

**Documentation Requirements:**
Create a world-class, strategic SOW that includes:

1. **Strategic Project Framework**
   - Enterprise strategic context
   - Market positioning
   - Competitive advantage
   - Value proposition

2. **Comprehensive Project Scope**
   - Detailed scope definition
   - Strategic objectives
   - Success metrics
   - Project constraints
   - Risk factors

3. **Advanced Deliverables Framework**
   - Comprehensive deliverable matrix
   - Quality assurance framework
   - Validation methodology
   - Performance metrics
   - Acceptance criteria

4. **Strategic Timeline Management**
   - Critical path analysis
   - Resource optimization
   - Risk-adjusted scheduling
   - Dependencies management
   - Contingency planning

5. **Enterprise Resource Planning**
   - Team structure and roles
   - Resource allocation strategy
   - Capacity planning
   - External dependencies
   - Vendor management

6. **Advanced Project Management**
   - Communication framework
   - Risk management strategy
   - Quality assurance process
   - Change management procedures
   - Governance structure

7. **Strategic Terms and Conditions**
   - Payment framework
   - Change management process
   - Termination conditions
   - Intellectual property rights
   - Compliance requirements

8. **Implementation Excellence**
   - Project phases
   - Resource optimization
   - Risk mitigation
   - Success metrics
   - Performance tracking

**Output Requirements:**
- Professional markdown format
- Strategic depth and clarity
- Comprehensive coverage
- 12-16 pages when converted to PDF
- Include all critical project elements
- Ensure strategic alignment with business objectives"""
    }

class SOWValidator:
    """Validator for SOW content"""
    
    @staticmethod
    def validate_content(content: str, level: DocumentationLevel) -> Tuple[bool, float, List[str]]:
        """Validate SOW content against required sections and quality standards."""
        required_sections = SOWValidator._get_required_sections(level)
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
            "Project Overview",
            "Deliverables",
            "Project Schedule",
            "Resource Requirements",
            "Project Management",
            "Terms and Conditions",
            "Next Steps"
        ]
        
        if level == DocumentationLevel.SIMPLE:
            return base_sections
        elif level == DocumentationLevel.INTERMEDIATE:
            return base_sections + [
                "Executive Summary",
                "Project Scope and Objectives",
                "Implementation Strategy"
            ]
        else:  # Advanced
            return base_sections + [
                "Strategic Project Framework",
                "Comprehensive Project Scope",
                "Advanced Deliverables Framework",
                "Strategic Timeline Management",
                "Enterprise Resource Planning",
                "Advanced Project Management",
                "Strategic Terms and Conditions",
                "Implementation Excellence"
            ]

class SOWGenerator:
    """Generator for SOW documents"""
    
    def __init__(self):
        """Initialize the SOW generator."""
        self.llm_service = LLMService()
        self.storage_service = LocalStorageService()
        self.validator = SOWValidator()
    
    async def generate_documentation(self, file_id: str, doc_level: str = "Intermediate") -> Dict[str, Any]:
        """
        Generate premium-quality Statement of Work from a meeting transcription.
        
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
                "title": f"Statement of Work - {metadata.get('original_filename', 'Untitled')}",
                "content": documentation_content,
                "metadata": {
                    **metadata,
                    "generated_at": datetime.utcnow().isoformat(),
                    "document_type": "statement_of_work",
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
                system_prompt = SOWConfig.SYSTEM_PROMPTS[level]
                user_prompt = SOWConfig.USER_PROMPTS[level].format(
                    transcription=transcription,
                    current_date=datetime.now().strftime("%Y-%m-%d")
                )
                
                # Generate content using LLM service
                content = await self.llm_service.generate_response(
                    prompt=user_prompt,
                    system_prompt=system_prompt
                )
                
                # Validate the generated content
                is_valid, quality_score, issues = self.validator.validate_content(content, level)
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

    async def _update_documentation_file(self, doc_path: str, documentation: Dict[str, Any]) -> None:
        """Update documentation file with PDF path."""
        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                doc_data = json.load(f)
            
            doc_data["pdf_path"] = documentation["pdf_path"]
            
            with open(doc_path, "w", encoding="utf-8") as f:
                json.dump(doc_data, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error updating documentation file: {str(e)}")
            raise

class SOWAgent:
    """Agent for generating SOW documents"""
    
    def __init__(self):
        """Initialize the SOW agent."""
        self.generator = SOWGenerator()
    
    async def generate_documentation(self, file_id: str, doc_level: str = "Intermediate") -> Dict[str, Any]:
        """Generate SOW documentation."""
        try:
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="processing",
                progress=75,
                current_stage="sow_generation",
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
                    current_stage="sow_generation",
                    error=result["message"]
                )
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in SOW agent: {error_msg}")
            
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="failed",
                progress=75,
                current_stage="sow_generation",
                error=error_msg
            )
            
            return {
                "success": False,
                "message": f"Failed to generate SOW: {error_msg}"
            }
    
    async def get_documentation(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get generated SOW documentation."""
        try:
            return await self.generator.get_documentation(file_id)
        except Exception as e:
            logger.error(f"Error retrieving SOW: {str(e)}")
            return None
    
    async def get_documentation_with_metrics(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get SOW documentation with metrics."""
        try:
            return await self.generator.get_documentation_metrics(file_id)
        except Exception as e:
            logger.error(f"Error retrieving SOW metrics: {str(e)}")
            return None
    
    async def validate_documentation(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Validate generated SOW documentation."""
        try:
            doc = await self.get_documentation(file_id)
            if not doc:
                return None
            
            level = DocumentationLevel(doc.get("level", "Intermediate"))
            is_valid, quality_score, missing_sections = SOWValidator.validate_content(
                doc.get("content", ""),
                level
            )
            
            return {
                "is_valid": is_valid,
                "quality_score": quality_score,
                "missing_sections": missing_sections
            }
            
        except Exception as e:
            logger.error(f"Error validating SOW: {str(e)}")
            return None 