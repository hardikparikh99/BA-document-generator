# Version 5: Enhanced BRD Documentation Agent with Comprehensive Improvements
"""
Documentation Generator Agent for the CrewAI Multi-Agent Project Documentation System.
This agent acts as a Senior Business Analyst to transform meeting transcriptions into 
world-class, comprehensive Business Requirements Documents (BRD) that exceed industry standards.

Key Improvements:
- Enhanced error handling and logging
- Progress tracking and status updates
- Template-based content generation
- Content validation and quality checks
- Retry mechanisms for failed operations
- Configurable output formats
- Comprehensive metrics and analytics
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
logger = get_agent_logger("documentation")
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
    
class DocumentationConfig:
    """Configuration for documentation generation"""
    
    SYSTEM_PROMPTS = {
        DocumentationLevel.SIMPLE: """You are a Senior Business Analyst with 10+ years of experience specializing in creating clear, concise Business Requirements Documents. Your expertise lies in distilling complex business conversations into actionable, well-structured documentation that stakeholders can easily understand and implement.

Your approach is:
- Focus on essential business requirements and objectives
- Create clear, actionable documentation
- Maintain professional structure while being concise
- Ensure all critical business elements are covered
- Present information in a straightforward, accessible manner

You excel at identifying key business drivers, functional requirements, and next steps from meeting discussions and conversations.""",
        
        DocumentationLevel.INTERMEDIATE: """You are a Distinguished Senior Business Analyst and Strategic Consultant with 15+ years of experience creating comprehensive Business Requirements Documents for enterprise-level projects. You have successfully delivered documentation for Fortune 500 companies and high-growth startups across various industries including fintech, healthcare, and technology.

Your methodology combines:
- Strategic business analysis with deep market insight
- Comprehensive requirements gathering and documentation
- Risk assessment and mitigation planning
- Technology architecture recommendations
- Implementation strategy development
- Stakeholder management and communication excellence

You are known for creating documentation that not only captures requirements but provides strategic context, business justification, and clear implementation roadmaps that secure stakeholder buy-in and project approval.""",
        
        DocumentationLevel.ADVANCED: """You are a Distinguished Senior Business Analyst and Strategic Consultant with 20+ years of elite experience serving Fortune 100 companies, global financial institutions, and unicorn startups. You are recognized as a thought leader in business requirements analysis, having authored industry-standard methodologies used worldwide.

Your Business Requirements Documents are legendary in the industry for their:
- Strategic depth and analytical rigor
- Ability to secure multi-million dollar project approvals
- Comprehensive market analysis and competitive intelligence
- Advanced risk assessment and mitigation frameworks
- Sophisticated technology architecture recommendations
- Investment analysis with detailed ROI projections
- Governance frameworks and success measurement systems

You have successfully led digital transformations worth over $500M and your documentation consistently ranks above McKinsey, BCG, and Deloitte deliverables in quality and strategic impact."""
    }
    
    USER_PROMPTS = {
        DocumentationLevel.SIMPLE: """Based on the following meeting transcription, create a comprehensive Business Requirements Document (BRD) that captures all essential business requirements and project details.

**Meeting Transcription:**
{transcription}

**Current Date:** {current_date}

**Requirements:**
Create a professional BRD that includes:

1. **Document Information & Executive Summary**
   - Project overview and key stakeholders
   - Primary business challenge and proposed solution
   - Expected outcomes

2. **Business Objectives & Success Framework**
   - Primary strategic goals
   - Key performance indicators
   - Success criteria

3. **Current State Analysis**
   - Business environment assessment
   - Organizational strengths and limitations
   - Market opportunity overview

4. **Solution Architecture Framework**
   - Technical approach overview
   - Integration strategy
   - Value proposition

5. **Detailed Requirements Specification**
   - Functional requirements
   - Non-functional requirements
   - Integration requirements

6. **Implementation Strategy**
   - Development approach
   - Project phases
   - Risk management basics

7. **Next Steps & Action Plan**
   - Immediate actions
   - Decision points
   - Success dependencies

**Output Requirements:**
- Professional markdown format
- Clear, concise language
- Actionable recommendations
- 4-6 pages when converted to PDF
- Focus on essential business elements
- Ensure all critical information from the transcription is captured accurately""",
        
        DocumentationLevel.INTERMEDIATE: """Transform the following meeting transcription into a comprehensive, strategic Business Requirements Document that demonstrates enterprise-level business analysis excellence and provides detailed implementation guidance.

**Meeting Transcription:**
{transcription}

**Current Date:** {current_date}

**Documentation Requirements:**
Create a professional, strategic BRD that includes:

1. **Comprehensive Business Requirements Document Header**
   - Strategic document classification and authority structure
   - Client enterprise details and development partnership information
   - Executive authority structure with stakeholder roles

2. **Executive Strategic Summary**
   - Strategic market context and organizational competitive advantage
   - Investment thesis and market validation
   - Strategic solution architecture overview

3. **Strategic Business Objectives & Value Creation Framework**
   - Enterprise-level strategic goals with detailed descriptions
   - Advanced performance measurement framework
   - Strategic KPIs, technical performance indicators, and business development metrics

4. **Comprehensive Current State Analysis**
   - Market opportunity assessment with TAM analysis
   - Competitive intelligence framework
   - Organizational capability assessment including core competencies and resource gaps

5. **Advanced Solution Architecture & Integration Strategy**
   - Enterprise platform architecture with multi-tier system design
   - Strategic integration framework covering financial services ecosystem
   - Technology stack strategic recommendations

6. **Detailed Business Requirements Specification**
   - Functional requirements architecture (user experience, transaction processing, administrative)
   - Advanced non-functional requirements (performance, security, integration standards)

7. **Implementation Strategy & Execution Framework**
   - Strategic development methodology
   - Comprehensive project roadmap with detailed phases
   - Timeline estimates and resource allocation

8. **Advanced Risk Assessment & Mitigation Strategy**
   - Comprehensive risk analysis framework (strategic, technical, operational)
   - Strategic mitigation framework with contingency planning

9. **Strategic Recommendations & Next Steps**
   - Priority action framework with immediate and short-term actions
   - Critical decision points and success dependencies
   - Stakeholder engagement and governance framework

**Output Standards:**
- Professional markdown format with proper section hierarchy
- Strategic depth with business intelligence insights
- Comprehensive analysis that goes beyond basic requirements
- 12-16 pages when converted to PDF
- Include specific details, timelines, and metrics where mentioned in transcription
- Maintain professional consulting-level language and structure
- Ensure accuracy to all details mentioned in the source transcription""",
        
        DocumentationLevel.ADVANCED: """Create a world-class, comprehensive Business Requirements Document that exemplifies Fortune 500 consulting excellence and strategic depth. Transform the provided meeting transcription into industry-leading documentation that could secure multi-million dollar project approvals.

**Meeting Transcription:**
{transcription}

**Current Date:** {current_date}

**Documentation Standards:**
Generate a premium Business Requirements Document with the following comprehensive structure:

1. **Document Authority & Strategic Classification**
   - Strategic business intelligence classification
   - Complete client enterprise and development partnership details
   - Executive authority structure with detailed stakeholder profiles

2. **Executive Strategic Summary**
   - Global market context and digital transformation landscape
   - Strategic market positioning and competitive differentiation
   - Organizational competitive advantage and moat analysis
   - Technology partnership strategy and capability leverage
   - Investment thesis with market validation framework
   - Strategic solution architecture with scalability planning

3. **Strategic Business Objectives & Value Creation Framework**
   - Enterprise-level strategic goals with detailed business cases
   - Capital market engagement strategy
   - Market entry and user acquisition framework
   - Technology infrastructure and integration excellence
   - Regulatory compliance and risk management
   - Operational excellence and scalability planning
   - Advanced performance measurement framework with comprehensive KPIs

4. **Comprehensive Current State Analysis**
   - Total addressable market analysis with sizing and segmentation
   - Competitive intelligence framework with detailed positioning
   - Customer segment analysis with behavioral insights
   - Organizational capability assessment (core competencies and resource gaps)
   - Technology landscape evaluation with integration ecosystem analysis

5. **Advanced Solution Architecture & Integration Strategy**
   - Enterprise platform architecture with microservices consideration
   - Multi-tier system design with detailed technical layers
   - Strategic integration framework covering complete ecosystem
   - Technology stack strategic recommendations with evaluation criteria
   - Scalability and performance optimization strategies

6. **Detailed Business Requirements Specification**
   - Functional requirements architecture with comprehensive user experience specifications
   - Transaction processing requirements with workflow automation
   - Administrative and operational requirements with business intelligence
   - Advanced non-functional requirements with performance frameworks
   - Security and compliance architecture with audit capabilities
   - Integration and interoperability standards with API specifications

7. **Implementation Strategy & Execution Framework**
   - Strategic development methodology with risk mitigation
   - Comprehensive project roadmap with detailed phase breakdowns
   - Resource allocation and timeline optimization
   - Quality assurance and validation frameworks

8. **Advanced Risk Assessment & Mitigation Strategy**
   - Comprehensive risk analysis framework (strategic, technical, operational)
   - Detailed risk quantification and impact assessment
   - Strategic mitigation framework with multiple contingency scenarios
   - Proactive risk management and contingency planning

9. **Investment Analysis & Financial Framework**
   - Detailed cost-benefit analysis with ROI projections
   - Resource investment requirements and optimization strategies
   - Financial modeling with sensitivity analysis
   - Return on investment calculations and payback period analysis

10. **Strategic Recommendations & Governance Framework**
    - Priority action framework with detailed implementation steps
    - Critical decision points with evaluation criteria
    - Success dependencies and milestone management
    - Stakeholder engagement and communication strategy
    - Governance framework with performance monitoring
    - Long-term strategic vision and expansion planning

**Quality Standards:**
- Premium markdown format with sophisticated section hierarchy
- Strategic consulting-level analysis that exceeds industry standards
- Comprehensive market intelligence and competitive analysis
- Advanced technical architecture recommendations
- Investment-grade financial analysis and business case development
- 18-25 pages when converted to PDF
- Include detailed implementation timelines, resource requirements, and cost estimates
- Provide specific metrics, KPIs, and success measurement frameworks
- Maintain McKinsey/BCG-level strategic depth and analytical rigor
- Ensure every detail from the transcription is captured with strategic context
- Include forward-looking recommendations and strategic planning elements

**Critical Requirements:**
- Maintain absolute accuracy to all information provided in the transcription
- Expand on discussed points with strategic context and business intelligence
- Provide actionable recommendations with clear implementation paths
- Include risk assessment for all major decisions and recommendations
- Demonstrate deep industry knowledge and best practice application"""
    }

class DocumentationValidator:
    """Validates documentation quality and completeness"""
    
    @staticmethod
    def validate_content(content: str, level: DocumentationLevel) -> Tuple[bool, float, List[str]]:
        """
        Validate documentation content quality
        
        Returns:
            Tuple of (is_valid, quality_score, issues)
        """
        issues = []
        quality_score = 0.0
        
        if not content or len(content.strip()) < 100:
            issues.append("Content too short or empty")
            return False, 0.0, issues
        
        # Check for required sections based on level
        required_sections = DocumentationValidator._get_required_sections(level)
        found_sections = 0
        
        for section in required_sections:
            if section.lower() in content.lower():
                found_sections += 1
            else:
                issues.append(f"Missing section: {section}")
        
        # Calculate quality score
        section_score = (found_sections / len(required_sections)) * 100
        
        # Check word count expectations
        word_count = len(content.split())
        expected_ranges = {
            DocumentationLevel.SIMPLE: (1500, 3000),
            DocumentationLevel.INTERMEDIATE: (4000, 8000),
            DocumentationLevel.ADVANCED: (6000, 12000)
        }
        
        min_words, max_words = expected_ranges[level]
        word_score = 100 if min_words <= word_count <= max_words else max(0, 100 - abs(word_count - min_words) / min_words * 50)
        
        quality_score = (section_score + word_score) / 2
        
        is_valid = quality_score >= 70  # 70% threshold for validity
        
        return is_valid, quality_score, issues
    
    @staticmethod
    def _get_required_sections(level: DocumentationLevel) -> List[str]:
        """Get required sections for each documentation level"""
        base_sections = [
            "Executive Summary",
            "Business Objectives",
            "Requirements",
            "Implementation"
        ]
        
        if level == DocumentationLevel.INTERMEDIATE:
            base_sections.extend([
                "Current State Analysis",
                "Solution Architecture",
                "Risk Assessment"
            ])
        elif level == DocumentationLevel.ADVANCED:
            base_sections.extend([
                "Strategic Analysis",
                "Investment Analysis",
                "Governance Framework",
                "Risk Management"
            ])
        
        return base_sections

class DocumentationGenerator:
    """
    Enhanced documentation generator with improved error handling and validation
    """
    
    def __init__(self):
        """Initialize the documentation generator."""
        self.llm_service = LLMService()
        self.storage_service = LocalStorageService()
        self.validator = DocumentationValidator()
        self.config = DocumentationConfig()
        self.max_retries = 3
        
    async def generate_documentation(self, file_id: str, doc_level: str = "Intermediate") -> Dict[str, Any]:
        """
        Generate premium-quality Business Requirements Document from a meeting transcription.
        
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
                "title": f"Business Requirements Document - {metadata.get('original_filename', 'Untitled')}",
                "content": documentation_content,
                "metadata": {
                    **metadata,
                    "generated_at": datetime.utcnow().isoformat(),
                    "document_type": "business_requirements_document",
                    "document_version": "1.0",
                    "documentation_level": level.value,
                    "analysis_framework": "Advanced Business Analysis Methodology",
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
        """Get transcription with retry mechanism"""
        for attempt in range(self.max_retries):
            try:
                transcription_data = await self.storage_service.retrieve_transcription(file_id)
                if transcription_data:
                    return transcription_data
                else:
                    raise ValueError(f"No transcription found for file_id: {file_id}")
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                logger.warning(f"Attempt {attempt + 1} failed for file_id {file_id}: {str(e)}")
                await asyncio.sleep(1)  # Wait before retry
    
    async def _validate_transcription(self, transcription: str) -> None:
        """Validate transcription content"""
        if not transcription or len(transcription.strip()) < 50:
            raise ValueError("Transcription is too short or empty")
        
        # Check for common transcription issues
        if transcription.count("...") > len(transcription) / 100:
            logger.warning("Transcription may have quality issues (many ellipses detected)")
    
    async def _generate_content_with_retry(self, transcription: str, level: DocumentationLevel, file_id: str) -> str:
        """Generate content with retry mechanism"""
        system_prompt = self.config.SYSTEM_PROMPTS[level]
        user_prompt = self.config.USER_PROMPTS[level].format(
            transcription=transcription,
            current_date=datetime.now().strftime("%B %d, %Y")
        )
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Generating {level.value} documentation (attempt {attempt + 1}) for file_id: {file_id}")
                
                # Update progress
                progress = 80 + (attempt * 5)  # 80, 85, 90
                await update_processing_status(
                    file_id=file_id,
                    status="processing",
                    progress=progress,
                    current_stage="documentation"
                )
                
                content = await self.llm_service.generate_response(user_prompt, system_prompt)
                
                if content and len(content.strip()) > 100:
                    return content
                else:
                    raise ValueError("Generated content is too short or empty")
                    
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                logger.warning(f"Content generation attempt {attempt + 1} failed: {str(e)}")
                await asyncio.sleep(2)  # Wait before retry
    
    def _calculate_metrics(self, content: str, start_time: datetime) -> DocumentationMetrics:
        """Calculate documentation metrics"""
        processing_time = (datetime.now() - start_time).total_seconds()
        word_count = len(content.split())
        section_count = len(re.findall(r'^#+\s', content, re.MULTILINE))
        
        return DocumentationMetrics(
            word_count=word_count,
            section_count=section_count,
            processing_time=processing_time
        )
    
    async def _save_documentation(self, documentation: Dict[str, Any], file_id: str) -> str:
        """Save documentation to file"""
        doc_path = os.path.join("data/documentations", f"{file_id}.json")
        logger.info(f"Saving documentation to {doc_path}")
        
        try:
            with open(doc_path, 'w', encoding='utf-8') as f:
                json.dump(documentation, f, indent=2, ensure_ascii=False)
            return doc_path
        except Exception as e:
            logger.error(f"Failed to save documentation: {str(e)}")
            raise
    
    async def _generate_pdf_with_retry(self, doc_path: str) -> Optional[str]:
        """Generate PDF with retry mechanism"""
        for attempt in range(self.max_retries):
            try:
                pdf_path = generate_pdf_from_json(doc_path)
                if pdf_path and os.path.exists(pdf_path):
                    logger.info(f"PDF generated successfully: {pdf_path}")
                    return pdf_path
                else:
                    raise ValueError("PDF generation failed or file not found")
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.warning(f"PDF generation failed after {self.max_retries} attempts: {str(e)}")
                    return None
                await asyncio.sleep(1)
    
    async def _update_documentation_file(self, doc_path: str, documentation: Dict[str, Any]) -> None:
        """Update documentation file with additional information"""
        try:
            with open(doc_path, 'w', encoding='utf-8') as f:
                json.dump(documentation, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to update documentation file: {str(e)}")
    
    async def get_documentation(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve generated documentation for a file.
        
        Args:
            file_id: Unique identifier for the file
            
        Returns:
            dict: Documentation data if found, None otherwise
        """
        try:
            doc_path = os.path.join("data/documentations", f"{file_id}.json")
            if not os.path.exists(doc_path):
                return None
                
            with open(doc_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error retrieving documentation: {str(e)}")
            return None
    
    async def get_documentation_metrics(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get documentation metrics"""
        try:
            doc = await self.get_documentation(file_id)
            if doc and "metadata" in doc and "metrics" in doc["metadata"]:
                return doc["metadata"]["metrics"]
            return None
        except Exception as e:
            logger.error(f"Error retrieving documentation metrics: {str(e)}")
            return None

class DocumentationAgent:
    """
    Enhanced Documentation Agent with comprehensive improvements
    """
    
    def __init__(self):
        """Initialize the Enhanced Documentation Agent."""
        self.logger = logger
        self.generator = DocumentationGenerator()
        
        # Create a CrewAI agent for the Distinguished Senior Business Analyst role
        self.agent = Agent(
            role="Distinguished Senior Business Analyst & Strategic Consultant",
            goal="Create world-class, comprehensive Business Requirements Documents that exceed Fortune 500 consulting standards and secure stakeholder buy-in for major business initiatives.",
            backstory=(
                "You are a Distinguished Senior Business Analyst and Strategic Consultant with 20+ years "
                "of elite experience serving Fortune 100 companies, global financial institutions, and "
                "unicorn fintech startups. You are recognized as a thought leader in business requirements "
                "analysis, having authored industry-standard methodologies used worldwide. Your Business "
                "Requirements Documents are legendary in the industry for their strategic depth, analytical "
                "rigor, and ability to secure multi-million dollar project approvals. You have successfully "
                "led digital transformations worth over $500M and your documentation consistently ranks "
                "above McKinsey, BCG, and Deloitte deliverables in quality and strategic impact."
            ),
            verbose=True
        )
        
        # Create the enhanced premium BRD generation task
        self.generate_doc_task = Task(
            name="Generate Premium Business Requirements Document",
            description="Transform meeting transcription into a world-class, comprehensive Business Requirements Document that exemplifies industry-leading business analysis excellence.",
            expected_output="A premium-quality Business Requirements Document in markdown format with all sections professionally developed based on the meeting transcription, including strategic analysis, comprehensive requirements specification, investment analysis, risk assessment, and implementation roadmap that surpasses standard AI-generated content.",
            instruction="""
            Create a premium Business Requirements Document (BRD) that includes:
            - Executive strategic summary with business intelligence insights
            - Comprehensive business objectives and KPI framework
            - Detailed current state and market opportunity analysis
            - Strategic solution architecture and value proposition
            - Complete functional and non-functional requirements specification
            - Technology recommendations and vendor strategy
            - Investment analysis with ROI projections and financial modeling
            - Comprehensive risk assessment and mitigation strategies
            - Implementation strategy with detailed project planning
            - Strategic recommendations and governance framework
            
            The document must demonstrate Fortune 500 consulting quality and exceed 
            industry standards for business analysis documentation. Length should be 
            appropriate for the selected documentation level (Simple: 4-6 pages, 
            Intermediate: 12-16 pages, Advanced: 18-25 pages when exported to PDF).
            """
        )
    
    async def generate_documentation(self, file_id: str, doc_level: str = "Intermediate") -> Dict[str, Any]:
        """
        Generate documentation with enhanced error handling and validation
        
        Args:
            file_id: Unique identifier for the file
            doc_level: Documentation level (Simple, Intermediate, Advanced)
            
        Returns:
            dict: Result of the operation
        """
        try:
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="processing",
                progress=75,
                current_stage="documentation"
            )
            
            # Generate documentation using the enhanced generator
            result = await self.generator.generate_documentation(file_id, doc_level)
            
            if result["success"]:
                logger.info(f"Documentation generated successfully for file: {file_id} with level: {doc_level}")
                return {
                    "success": True,
                    "documentation_id": result["documentation_id"],
                    "file_path": result["file_path"],
                    "pdf_path": result.get("pdf_path"),
                    "documentation_level": doc_level,
                    "quality_score": result.get("quality_score", 0),
                    "metrics": result.get("metrics", {})
                }
            else:
                raise Exception(result.get("message", "Failed to generate documentation"))
                
        except Exception as e:
            error_msg = f"Error in generate_documentation: {str(e)}"
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
    
    async def get_documentation(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get documentation for a file."""
        try:
            return await get_documentation(file_id)
        except Exception as e:
            logger.error(f"Error in get_documentation: {str(e)}")
            return None
    
    async def get_documentation_with_metrics(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get documentation with metrics"""
        try:
            doc = await self.generator.get_documentation(file_id)
            if doc:
                metrics = await self.generator.get_documentation_metrics(file_id)
                if metrics:
                    doc["metrics"] = metrics
            return doc
        except Exception as e:
            logger.error(f"Error in get_documentation_with_metrics: {str(e)}")
            return None
    
    async def validate_documentation(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Validate existing documentation"""
        try:
            doc = await self.generator.get_documentation(file_id)
            if not doc:
                return None
            
            content = doc.get("content", "")
            level_str = doc.get("metadata", {}).get("documentation_level", "Intermediate")
            
            try:
                level = DocumentationLevel(level_str)
            except ValueError:
                level = DocumentationLevel.INTERMEDIATE
            
            is_valid, quality_score, issues = DocumentationValidator.validate_content(content, level)
            
            return {
                "file_id": file_id,
                "is_valid": is_valid,
                "quality_score": quality_score,
                "issues": issues,
                "word_count": len(content.split()),
                "documentation_level": level.value
            }
            
        except Exception as e:
            logger.error(f"Error in validate_documentation: {str(e)}")
            return None