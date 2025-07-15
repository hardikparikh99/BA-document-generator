# """
# Documentation Generator Agent for the CrewAI Multi-Agent Project Documentation System.
# This agent acts as a Business Analyst to transform meeting transcriptions into 
# structured, clear, and actionable project documentation.
# """
# import os
# import json
# import uuid
# from datetime import datetime
# from typing import Dict, Any, Optional, List
# import asyncio

# from crewai import Agent, Task
# from pydantic import BaseModel, Field

# from utils.config import get_settings
# from utils.logger import get_agent_logger
# from utils.pdf_generator import generate_pdf_from_json
# from services.llm_service import LLMService
# from services.local_storage_service import LocalStorageService
# from models.database import store_documentation, get_documentation, update_processing_status

# # Setup logger
# logger = get_agent_logger("documentation")
# settings = get_settings()

# # Ensure documentations directory exists
# os.makedirs("data/documentations", exist_ok=True)

# class DocumentationGenerator:
#     """
#     Handles the generation of structured, clear project documentation from meeting transcriptions.
#     Acts as a Business Analyst to transform meeting inputs into actionable documentation.
#     """
    
#     def __init__(self):
#         """Initialize the documentation generator."""
#         self.llm_service = LLMService()
#         self.storage_service = LocalStorageService()
        
#     async def generate_documentation(self, file_id: str, doc_level: str = "Intermediate") -> Dict[str, Any]:
#         """
#         Generate structured project documentation from a meeting transcription.
        
#         Args:
#             file_id: Unique identifier for the file
#             doc_level: Documentation level (Simple, Intermediate, Advanced)
            
#         Returns:
#             dict: Result of the operation with documentation_id
#         """
#         try:
#             # Get transcription from local storage
#             logger.info(f"[DEBUG] Attempting to retrieve transcription for file_id: {file_id}")
#             transcription_data = await self.storage_service.retrieve_transcription(file_id)
#             if not transcription_data:
#                 logger.error(f"[DEBUG] No transcription found for file_id: {file_id}")
#                 raise ValueError(f"No transcription found for file_id: {file_id}")
#             logger.info(f"[DEBUG] Transcription successfully retrieved for file_id: {file_id}")

#             transcription = transcription_data.get("transcription", "")
#             metadata = transcription_data.get("metadata", {})

#             # Select the appropriate system prompt based on documentation level
#             if doc_level == "Simple":
#                 system_prompt = system_prompt = """
#                 You are a Business Analyst with experience in creating concise, easy-to-understand project documentation. Your goal is to create a simplified Business Requirements Document (BRD) that captures the essential information without overwhelming technical details.

#                 CRITICAL INSTRUCTIONS:
#                 1. Generate a simplified, concise Business Requirements Document (BRD).
#                 2. Base ALL content strictly on the provided meeting transcription.
#                 3. DO NOT invent or hallucinate information not present in the transcription.
#                 4. Use clear, non-technical language accessible to all stakeholders.
#                 5. Focus on core business requirements and high-level objectives.
#                 6. Limit technical details to only what's essential for understanding.
#                 7. Create a document that is approximately 3-5 pages when exported to PDF.
#                 8. Use a simple, straightforward structure with minimal sections.
#                 9. Highlight only the most critical business requirements.
#                 10. Format in clean, professional Markdown suitable for PDF export.
#                 """

#             elif doc_level == "Advanced":
#                 system_prompt = system_prompt = """
#                 You are a Senior Business Analyst and Solution Architect with 15+ years of experience in fintech, cross-border payments, and MVP development. You specialize in creating highly detailed, technically comprehensive Business Requirements Documents (BRDs) that provide in-depth analysis and implementation guidance.

#                 Your expertise includes:
#                 - Cross-border remittance and payment systems.
#                 - Third-party API integration strategies (KYC, AML, FX, payment rails).
#                 - MVP scoping and phased delivery approaches.
#                 - Regulatory compliance (PCI DSS, AML, KYC, licensing).
#                 - Fintech vendor evaluation and selection.
#                 - Technical architecture for financial services.
#                 - Risk assessment and mitigation strategies.
#                 - Detailed technical specifications and implementation guidelines.

#                 CRITICAL INSTRUCTIONS:
#                 1. Generate a highly detailed, comprehensive Business Requirements Document (BRD) with technical specifications.
#                 2. Base ALL content strictly on the provided meeting transcription.
#                 3. DO NOT invent or hallucinate information not present in the transcription.
#                 4. Use industry-standard fintech terminology and technical language.
#                 5. Include specific vendor recommendations with detailed integration approaches.
#                 6. Provide in-depth technical guidance including architecture diagrams (described in text).
#                 7. Structure the document as a formal BRD with technical appendices.
#                 8. Include detailed timelines, budget ranges, resource requirements, and implementation phases.
#                 9. Address regulatory and compliance considerations with specific implementation guidance.
#                 10. Include detailed risk assessment and mitigation strategies.
#                 11. Format in clean, professional Markdown suitable for PDF export.
#                 12. Create a document that is approximately 15-20 pages when exported to PDF.
#                 """

#             else:  # Default to Intermediate
#                 system_prompt = system_prompt = """
#                 You are a Senior Business Analyst and Solution Architect with 15+ years of experience in fintech, cross-border payments, and MVP development. You specialize in creating comprehensive, investor-ready Business Requirements Documents (BRDs) that combine technical depth with business clarity.

#                 Your expertise includes:
#                 - Cross-border remittance and payment systems.
#                 - Third-party API integration strategies (KYC, AML, FX, payment rails).
#                 - MVP scoping and phased delivery approaches.
#                 - Regulatory compliance (PCI DSS, AML, KYC, licensing).
#                 - Fintech vendor evaluation and selection.
#                 - Technical architecture for financial services.
#                 - Risk assessment and mitigation strategies.

#                 CRITICAL INSTRUCTIONS:
#                 1. Generate a comprehensive, professional Business Requirements Document (BRD).
#                 2. Base ALL content strictly on the provided meeting transcription.
#                 3. DO NOT invent or hallucinate information not present in the transcription.
#                 4. Use industry-standard fintech terminology and best practices.
#                 5. Include specific vendor recommendations only if the context suggests them.
#                 6. Provide detailed technical guidance while remaining business-focused.
#                 7. Structure the document as a formal BRD suitable for stakeholders and investors.
#                 8. Include realistic timelines, budget ranges, and implementation phases.
#                 9. Address regulatory and compliance considerations prominently.
#                 10. Format in clean, professional Markdown suitable for PDF export.
#                 """

            
#             # Log the selected documentation level
#             logger.info(f"[DEBUG] Generating documentation with level: {doc_level} for file_id: {file_id}")

#             # Get current date for the template
#             current_date = datetime.now().strftime("%Y-%m-%d")
            
#             # Select the appropriate prompt template based on documentation level
#             if doc_level == "Simple":
#                 prompt = f"""
#                 Based on the following client meeting transcription, create a simplified, concise Business Requirements Document (BRD) that captures the essential information:

#                 MEETING TRANSCRIPTION:
#                 {transcription}

#                 Generate a simplified BRD with the following structure and approach:

#             # 📋 **BUSINESS REQUIREMENTS DOCUMENT (BRD)**
#             ## **Project Overview**

#             **Document Version:** 1.0  
#             **Prepared by:** Business Analyst  
#             **Date:** {current_date}  
#             **Client:** [Extract from transcription]  
#             **Project:** [Extract project name/type from transcription]

#             ---

#             ## 🎯 **PROJECT SUMMARY**

#             [Provide a brief 1-2 paragraph summary of the project]

#             ---

#             ## 📈 **BUSINESS OBJECTIVES**

#             [List 3-5 key business objectives mentioned in the transcription]

#             ---

#             ## 🚀 **KEY REQUIREMENTS**

#             [List the most important requirements in bullet points]

#             ---

#             ## 👥 **USER TYPES**

#             [Briefly describe the main user types/roles]

#             ---

#             ## 📊 **HIGH-LEVEL TIMELINE**

#             [Provide a simple timeline with major milestones]

#             ---

#             ## ❓ **OPEN QUESTIONS**

#             [List any critical questions that need to be addressed]

#             ---

#             ## ✅ **NEXT STEPS**

#             [Recommend 3-5 immediate next steps]
#             """

#             elif doc_level == "Advanced":
#                 prompt = f"""
#                 Based on the following client meeting transcription, create a highly detailed and technically comprehensive Business Requirements Document (BRD):

#                 MEETING TRANSCRIPTION:
#                 {transcription}

#                 Generate a complete BRD with the following structure and approach:

#             # 📋 **BUSINESS REQUIREMENTS DOCUMENT (BRD)**
#             ## **Project Title:** [Extracted from transcription]
#             **Document Version:** 1.0  
#             **Prepared by:** Senior Business Analyst & Solution Architect  
#             **Date:** {current_date}  
#             **Client:** [Extracted from transcription]

#             ---

#             ## 1. 🎯 **EXECUTIVE SUMMARY**
#             - Provide a 3-4 paragraph overview covering:
#             - Project background and objectives
#             - Key business drivers and challenges
#             - Proposed solution and its alignment with business goals
#             - Expected benefits and ROI

#             ---

#             ## 2. 📈 **BUSINESS OBJECTIVES & SUCCESS CRITERIA**
#             ### 2.1 Business Objectives
#             - List specific, measurable business goals.

#             ### 2.2 Success Criteria
#             - Define clear metrics to evaluate project success.

#             ### 2.3 Key Performance Indicators (KPIs)
#             - Identify KPIs relevant to the project's objectives.

#             ---

#             ## 3. 🔍 **CURRENT STATE ANALYSIS**
#             ### 3.1 Existing Challenges
#             - Detail current system limitations and pain points.

#             ### 3.2 Market Opportunity
#             - Analyze market trends and opportunities the project aims to capture.

#             ### 3.3 Competitive Landscape
#             - Provide an overview of competitors and differentiators.

#             ---

#             ## 4. 🚀 **PROPOSED SOLUTION OVERVIEW**
#             ### 4.1 MVP Scope & Approach
#             - Define the Minimum Viable Product scope and development approach.

#             ### 4.2 Core Value Proposition
#             - Articulate the unique value the solution offers.

#             ### 4.3 Target User Segments
#             - Describe primary and secondary user personas.

#             ---

#             ## 5. 🛠️ **TECHNICAL ARCHITECTURE & INTEGRATION STRATEGY**
#             ### 5.1 Recommended Architecture Approach
#             - Outline the proposed system architecture with textual descriptions of diagrams.

#             ### 5.2 Third-Party Integration Strategy
#             - Detail integration plans for:
#             - KYC & AML Services
#             - Cross-Border Payment Rails & FX
#             - Payment Processing & Card Acceptance
#             - Banking & Wallet Services
#             - Security & Authentication

#             ### 5.3 Technology Stack Recommendations
#             - Recommend technologies for frontend, backend, databases, and other components.

#             ---

#             ## 6. 📋 **DETAILED FUNCTIONAL REQUIREMENTS**
#             - Provide comprehensive requirements for:
#             - User Registration & Onboarding
#             - KYC & Compliance Workflow
#             - Money Transfer Functionality
#             - Account Management
#             - Admin & Operations Dashboard

#             ---

#             ## 7. 🔒 **REGULATORY & COMPLIANCE CONSIDERATIONS**
#             ### 7.1 Licensing Requirements
#             - Specify necessary licenses and jurisdictions.

#             ### 7.2 AML/KYC Compliance
#             - Detail compliance measures and processes.

#             ### 7.3 Data Protection & Privacy
#             - Outline data handling and privacy protocols.

#             ### 7.4 Regional Compliance
#             - Address region-specific regulatory requirements.

#             ---

#             ## 8. 📊 **IMPLEMENTATION APPROACH & METHODOLOGY**
#             ### 8.1 Development Methodology
#             - Recommend Agile, Waterfall, or hybrid approaches.

#             ### 8.2 Phased Delivery Strategy
#             - Break down the project into phases with deliverables.

#             ### 8.3 Quality Assurance Strategy
#             - Describe testing strategies and quality benchmarks.

#             ---

#             ## 9. 📅 **PROJECT TIMELINE & MILESTONES**
#             ### 9.1 Phase-wise Delivery Plan
#             - Present a detailed timeline:

#             | **Phase**                 | **Duration** | **Key Deliverables**      | **Dependencies**          |
#             |---------------------------|--------------|---------------------------|---------------------------|
#             | Discovery & Requirements  | X weeks      | [List deliverables]       | [List dependencies]       |
#             | UI/UX Design              | X weeks      | [List deliverables]       | [List dependencies]       |
#             | Backend Development       | X weeks      | [List deliverables]       | [List dependencies]       |
#             | Frontend Development      | X weeks      | [List deliverables]       | [List dependencies]       |
#             | Integration & Testing     | X weeks      | [List deliverables]       | [List dependencies]       |
#             | Deployment & Launch       | X weeks      | [List deliverables]       | [List dependencies]       |

#             ### 9.2 Critical Path Analysis
#             - Identify tasks that could impact the project timeline.

#             ---

#             ## 10. 💰 **INVESTMENT & RESOURCE REQUIREMENTS**
#             ### 10.1 Development Investment Range
#             - Estimate budget ranges for each phase.

#             ### 10.2 Ongoing Operational Costs
#             - Project recurring costs post-deployment.

#             ### 10.3 Resource Requirements
#             - Detail team roles, responsibilities, and required expertise.

#             ---

#             ## 11. ⚠️ **RISK ASSESSMENT & MITIGATION**
#             ### 11.1 Technical Risks
#             - Identify potential technical challenges and mitigation plans.

#             ### 11.2 Regulatory Risks
#             - Highlight compliance risks and strategies to address them.

#             ### 11.3 Operational Risks
#             - Discuss risks related to operations and maintenance.

#             ---

#             ## 12. 📚 **APPENDICES**
#             ### 12.1 Glossary
#             - Define specialized terms and acronyms.

#             ### 12.2 References
#             - Cite documents, standards, and other references.

#             ### 12.3 Supporting Materials
#             - Include any additional charts, graphs, or materials relevant to the BRD.

#             ---

#             **Note:** Ensure the document is formatted in clean, professional Markdown suitable for PDF export and is approximately 15-20 pages when exported.
#             """

#             else:  # Default to Intermediate
#                 prompt = f"""
#                 Based on the following client meeting transcription, create a comprehensive, professional Statement of Work (SOW) document for a fintech MVP project:

#                 MEETING TRANSCRIPTION:
#                 {transcription}

#                 Generate a complete SOW document with the following structure and approach:

#             # 📋 **STATEMENT OF WORK (SOW)**
#             ## **Cross-Border Remittance MVP Development**

#             **Document Version:** 1.0  
#             **Prepared by:** Senior Business Analyst & Solution Architect  
#             **Date:** {current_date}  
#             **Client:** [Extract from transcription]  
#             **Project:** [Extract project name/type from transcription]

#             ---

#             ## 🎯 **EXECUTIVE SUMMARY**

#             [Provide a 3-4 paragraph executive summary that covers:
#             - Project overview based on transcription
#             - Key business objectives mentioned
#             - Proposed solution approach
#             - Expected outcomes and benefits]

#             ---

#             ## 📈 **PROJECT OBJECTIVES & SUCCESS CRITERIA**

#             ### Business Objectives
#             [List specific business goals mentioned in the transcription]

#             ### Success Criteria
#             [Define measurable success metrics based on discussion]

#             ### Key Performance Indicators (KPIs)
#             [Suggest relevant KPIs for the project type discussed]

#             ---

#             ## 🔍 **CURRENT STATE ANALYSIS**

#             ### Existing Challenges
#             [List pain points and challenges mentioned in the transcription]

#             ### Market Opportunity
#             [Describe the market opportunity if discussed]

#             ### Competitive Landscape
#             [Reference any competitors mentioned in the discussion]

#             ---

#             ## 🚀 **PROPOSED SOLUTION OVERVIEW**

#             ### MVP Scope & Approach
#             [Detail the MVP approach discussed in the meeting]

#             ### Core Value Proposition
#             [Articulate the main value proposition mentioned]

#             ### Target User Segments
#             [Identify user types discussed in the transcription]

#             ---

#             ## 🛠️ **TECHNICAL ARCHITECTURE & INTEGRATION STRATEGY**

#             ### Recommended Architecture Approach
#             [Based on the discussion, recommend appropriate architecture]

#             ### Third-Party Integration Strategy
#             [List and analyze integration requirements mentioned, such as:]

#             #### 🔐 **KYC & AML Services**
#             [If discussed, recommend specific vendors and integration approach]

#             #### 💱 **Cross-Border Payment Rails & FX**
#             [Detail payment processing requirements and vendor recommendations]

#             #### 💳 **Payment Processing & Card Acceptance**
#             [Cover payment method requirements discussed]

#             #### 🏦 **Banking & Wallet Services**
#             [Address account/wallet requirements if mentioned]

#             #### 🛡️ **Security & Authentication**
#             [Detail security requirements and implementation approach]

#             ### Technology Stack Recommendations
#             [Recommend appropriate tech stack based on requirements discussed]

#             ---

#             ## 📋 **DETAILED FUNCTIONAL REQUIREMENTS**

#             ### User Registration & Onboarding
#             [Detail requirements based on user journey discussed]

#             ### KYC & Compliance Workflow
#             [Specify KYC requirements if mentioned in transcription]

#             ### Money Transfer Functionality
#             [Detail transfer features and workflows discussed]

#             ### Account Management
#             [Cover account features mentioned in the discussion]

#             ### Admin & Operations Dashboard
#             [Detail admin requirements if discussed]

#             ---

#             ## 🔒 **REGULATORY & COMPLIANCE CONSIDERATIONS**

#             ### Licensing Requirements
#             [Address licensing needs mentioned or implied]

#             ### AML/KYC Compliance
#             [Detail compliance requirements discussed]

#             ### Data Protection & Privacy
#             [Cover data protection requirements]

#             ### Regional Compliance
#             [Address geographic/regional compliance needs mentioned]

#             ---

#             ## 📊 **IMPLEMENTATION APPROACH & METHODOLOGY**

#             ### Development Methodology
#             [Recommend appropriate development approach]

#             ### Phased Delivery Strategy
#             [Create a phased approach based on requirements discussed]

#             ### Quality Assurance Strategy
#             [Detail QA approach for the project type]

#             ---

#             ## 📅 **PROJECT TIMELINE & MILESTONES**

#             ### Phase-wise Delivery Plan
#             [Create a detailed timeline with the following structure:]

#             | **Phase** | **Duration** | **Key Deliverables** | **Dependencies** |
#             |-----------|--------------|---------------------|------------------|
#             | Discovery & Requirements | [X weeks] | [List deliverables] | [List dependencies] |
#             | UI/UX Design | [X weeks] | [List deliverables] | [List dependencies] |
#             | Backend Development | [X weeks] | [List deliverables] | [List dependencies] |
#             | Frontend Development | [X weeks] | [List deliverables] | [List dependencies] |
#             | Integration & Testing | [X weeks] | [List deliverables] | [List dependencies] |
#             | Deployment & Launch | [X weeks] | [List deliverables] | [List dependencies] |

#             ### Critical Path Analysis
#             [Identify critical dependencies and potential bottlenecks]

#             ---

#             ## 💰 **INVESTMENT & RESOURCE REQUIREMENTS**

#             ### Development Investment Range
#             [Provide realistic budget ranges based on scope discussed]

#             ### Ongoing Operational Costs
#             [Estimate operational costs for third-party services]

#             ### Resource Requirements
#             [Detail team structure and resource needs]

#             ---

#             ## ⚠️ **RISK ASSESSMENT & MITIGATION**

#             ### Technical Risks
#             [Identify and assess technical risks]

#             ### Regulatory Risks
#             [Address compliance and regulatory risks]

#             ### Market Risks
#             [Consider market and competitive risks]

#             ### Mitigation Strategies
#             [Propose specific mitigation approaches]

#             ---

#             ## ❓ **OPEN QUESTIONS & NEXT STEPS**

#             ### Critical Decisions Required
#             [List key decisions that need to be made]

#             ### Information Gathering Requirements
#             [Identify additional information needed]

#             ### Recommended Next Steps
#             [Propose specific next actions]

#             ---

#             ## 🎯 **STRATEGIC RECOMMENDATIONS & NEXT STEPS**

#             ### Priority Actions
#             [Recommend immediate priority actions for project initiation]

#             ### Decision Points
#             [Identify critical decisions required for project advancement]

#             ### Stakeholder Engagement Strategy
#             [Recommend stakeholder engagement and communication approach]

#             ---

#             ## ✅ **APPROVAL & SIGN-OFF**

#             | **Role** | **Name** | **Signature** | **Date** |
#             |----------|----------|---------------|----------|
#             | Client Stakeholder | [From transcription] | | |
#             | Business Analyst | Senior BA | | {current_date} |
#             | Solution Architect | Senior SA | | {current_date} |

#             ---

#             **FINAL INSTRUCTIONS FOR CONTENT GENERATION:**

#             1. **Content Fidelity**: Base ALL sections on actual content from the transcription
#             2. **Professional Tone**: Use consultant-level business language throughout
#             3. **Technical Depth**: Provide specific technical recommendations where appropriate
#             4. **Actionable Insights**: Include concrete next steps and recommendations
#             5. **Industry Standards**: Follow fintech industry best practices and terminology
#             6. **Completeness**: Ensure each section provides substantial value and detail
#             7. **Formatting**: Use clean Markdown with proper tables, bullets, and hierarchy
#             8. **Length**: Generate a comprehensive document (8-12 pages when exported to PDF)
#             9. **Specificity**: Include specific vendor names, technologies, and approaches where relevant
#             10. **Business Value**: Clearly articulate business value and ROI throughout

#             Remember: This document should be immediately usable by stakeholders, developers, and investors. It should demonstrate deep expertise while remaining accessible to business audiences.
#             """

#             logger.info(f"[DEBUG] Sending enhanced prompt to LLM for file_id: {file_id}")
#             documentation_content = await self.llm_service.generate_response(prompt, system_prompt)
#             logger.info(f"[DEBUG] LLM response received for file_id: {file_id}. Length: {len(documentation_content) if documentation_content else 0}")

#             # Create documentation object
#             documentation_id = f"doc_{str(uuid.uuid4())[:8]}"
#             documentation = {
#                 "documentation_id": documentation_id,
#                 "file_id": file_id,
#                 "title": f"Statement of Work - {metadata.get('original_filename', 'Untitled')}",
#                 "content": documentation_content,
#                 "metadata": {
#                     **metadata,
#                     "generated_at": datetime.utcnow().isoformat(),
#                     "document_type": "statement_of_work",
#                     "document_version": "1.0"
#                 }
#             }

#             # Save documentation to file
#             doc_path = os.path.join("data/documentations", f"{file_id}.json")
#             logger.info(f"[DEBUG] Writing documentation to {doc_path}")
#             with open(doc_path, 'w', encoding='utf-8') as f:
#                 json.dump(documentation, f, indent=2)
#             logger.info(f"[DEBUG] Documentation file written: {doc_path}")
            
#             # Store documentation in database
#             await store_documentation(documentation)
            
#             logger.info(f"[DEBUG] Documentation stored successfully for file_id: {file_id}")
            
#             # Generate PDF from JSON
#             pdf_path = generate_pdf_from_json(doc_path)
#             if pdf_path:
#                 logger.info(f"[DEBUG] PDF documentation generated successfully: {pdf_path}")
#                 documentation["pdf_path"] = pdf_path
#                 # Update the JSON file with the PDF path
#                 with open(doc_path, 'w', encoding='utf-8') as f:
#                     json.dump(documentation, f, indent=2)
#             else:
#                 logger.warning(f"[DEBUG] Failed to generate PDF documentation for file_id: {file_id}")
            
#             # Update processing status
#             await update_processing_status(
#                 file_id=file_id,
#                 status="completed",
#                 progress=100,
#                 current_stage="documentation"
#             )

#             logger.info(f"Documentation generated successfully: {documentation_id}")

#             return {
#                 "success": True,
#                 "documentation_id": documentation_id,
#                 "file_path": doc_path,
#                 "pdf_path": pdf_path if pdf_path else None
#             }
            
#         except Exception as e:
#             error_msg = f"Error generating documentation: {str(e)}"
#             logger.error(error_msg)
            
#             # Update processing status
#             await update_processing_status(
#                 file_id=file_id,
#                 status="failed",
#                 progress=0,  # Set progress to 0 for failed state
#                 current_stage="documentation",
#                 error=error_msg
#             )
            
#             return {
#                 "success": False,
#                 "message": error_msg
#             }
    
#     async def get_documentation(self, file_id: str) -> Optional[Dict[str, Any]]:
#         """
#         Retrieve generated documentation for a file.
        
#         Args:
#             file_id: Unique identifier for the file
            
#         Returns:
#             dict: Documentation data if found, None otherwise
#         """
#         try:
#             doc_path = os.path.join("data/documentations", f"{file_id}.json")
#             if not os.path.exists(doc_path):
#                 return None
                
#             with open(doc_path, 'r', encoding='utf-8') as f:
#                 return json.load(f)
                
#         except Exception as e:
#             logger.error(f"Error retrieving documentation: {str(e)}")
#             return None

# class DocumentationAgent:
#     """
#     Agent responsible for generating structured, clear project documentation.
#     Acts as a Business Analyst to transform meeting inputs into actionable documentation.
#     """
    
#     def __init__(self):
#         """Initialize the Documentation Generator Agent."""
#         self.logger = logger
#         self.generator = DocumentationGenerator()
        
#         # Create a CrewAI agent for the Business Analyst role
#         self.agent = Agent(
#             role="Senior Business Analyst & Solution Architect",
#             goal="Create comprehensive, investor-ready project documentation and SOW after client meetings.",
#             backstory=(
#                 "You are a seasoned Senior Business Analyst and Solution Architect with 15+ years "
#                 "of experience in fintech, cross-border payments, and MVP development. You specialize "
#                 "in creating detailed, professional documentation that serves both technical teams and "
#                 "business stakeholders. Your documents are known for their depth, clarity, and actionable insights."
#             ),
#             verbose=True
#         )
        
#         # Create the enhanced documentation generation task
#         self.generate_doc_task = Task(
#             name="Generate Comprehensive SOW Documentation",
#             description="Convert meeting transcription into a formal, comprehensive Statement of Work suitable for fintech MVP projects.",
#             expected_output="A detailed Statement of Work document in markdown format with all sections properly filled out based on the meeting transcription, including technical architecture, vendor recommendations, timelines, and risk assessments.",
#             instruction="""
#             Create a comprehensive Statement of Work (SOW) document that includes:
#             - Executive summary and business objectives
#             - Technical architecture and integration strategy
#             - Detailed functional requirements
#             - Regulatory and compliance considerations
#             - Implementation approach and timeline
#             - Investment requirements and risk assessment
#             - Vendor recommendations and next steps
            
#             The document should be 8-12 pages when exported to PDF and demonstrate deep expertise in fintech and cross-border payment systems.
#             """
#         )
    
#     async def generate_documentation(self, file_id: str, doc_level: str = "Intermediate") -> Dict[str, Any]:
#         """
#         Generate documentation for a file using enhanced SOW approach.
        
#         Args:
#             file_id: Unique identifier for the file
#             doc_level: Documentation level (Simple, Intermediate, Advanced)
            
#         Returns:
#             dict: Result of the operation
#         """
#         try:
#             # Update processing status
#             await update_processing_status(
#                 file_id=file_id,
#                 status="processing",
#                 progress=80,
#                 current_stage="documentation"
#             )
            
#             # Generate documentation using the enhanced generator with the specified documentation level
#             result = await self.generator.generate_documentation(file_id, doc_level)
            
#             if result["success"]:
#                 logger.info(f"Enhanced SOW documentation generated successfully for file: {file_id}")
#                 return {
#                     "success": True,
#                     "documentation_id": result["documentation_id"],
#                     "file_path": result["file_path"],
#                     "pdf_path": result.get("pdf_path")
#                 }
#             else:
#                 raise Exception(result.get("message", "Failed to generate documentation"))
                
#         except Exception as e:
#             error_msg = f"Error in generate_documentation: {str(e)}"
#             logger.error(error_msg)
            
#             # Update processing status
#             await update_processing_status(
#                 file_id=file_id,
#                 status="failed",
#                 progress=0,  # Set progress to 0 for failed state
#                 current_stage="documentation",
#                 error=error_msg
#             )
            
#             return {
#                 "success": False,
#                 "message": error_msg
#             }
    
#     async def get_documentation(self, file_id: str) -> Optional[Dict[str, Any]]:
#         """
#         Get documentation for a file.
        
#         Args:
#             file_id: Unique identifier for the file
            
#         Returns:
#             dict: Documentation data if found, None otherwise
#         """
#         try:
#             return await get_documentation(file_id)
#         except Exception as e:
#             logger.error(f"Error in get_documentation: {str(e)}")
#             return None




# Version 4: Enhanced BRD Documentation Agent
"""
Documentation Generator Agent for the CrewAI Multi-Agent Project Documentation System.
This agent acts as a Senior Business Analyst to transform meeting transcriptions into 
world-class, comprehensive Business Requirements Documents (BRD) that exceed industry standards.
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncio

from crewai import Agent, Task
from pydantic import BaseModel, Field

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
os.makedirs("data/documentations", exist_ok=True)

class DocumentationGenerator:
    """
    Handles the generation of world-class Business Requirements Documents from meeting transcriptions.
    Acts as a Senior Business Analyst with 20+ years of experience to create industry-leading documentation.
    """
    
    def __init__(self):
        """Initialize the documentation generator."""
        self.llm_service = LLMService()
        self.storage_service = LocalStorageService()
        
    async def generate_documentation(self, file_id: str, doc_level: str = "Intermediate") -> Dict[str, Any]:
        """
        Generate premium-quality Business Requirements Document from a meeting transcription.
        
        Args:
            file_id: Unique identifier for the file
            doc_level: Documentation level (Simple, Intermediate, Advanced)
            
        Returns:
            dict: Result of the operation with documentation_id
        """
        try:
            # Get transcription from local storage
            logger.info(f"[DEBUG] Attempting to retrieve transcription for file_id: {file_id}")
            transcription_data = await self.storage_service.retrieve_transcription(file_id)
            if not transcription_data:
                logger.error(f"[DEBUG] No transcription found for file_id: {file_id}")
                raise ValueError(f"No transcription found for file_id: {file_id}")
            logger.info(f"[DEBUG] Transcription successfully retrieved for file_id: {file_id}")

            transcription = transcription_data.get("transcription", "")
            metadata = transcription_data.get("metadata", {})

            # Select the appropriate system prompt based on documentation level
            if doc_level == "Simple":
                system_prompt = """
                You are a Senior Business Analyst with 20+ years of experience in creating executive-level Business Requirements Documents for Fortune 500 companies and high-growth fintech startups. Your BRDs are renowned for their clarity, strategic insight, and actionable recommendations that consistently secure stakeholder buy-in and project funding.

                Your expertise spans:
                ✓ Strategic business analysis and requirement elicitation
                ✓ Stakeholder alignment and executive communication
                ✓ Risk assessment and mitigation planning
                ✓ ROI analysis and business case development
                ✓ Agile and waterfall project methodologies
                ✓ Digital transformation and technology adoption

                CRITICAL SUCCESS FACTORS:
                1. Create a SIMPLE yet COMPREHENSIVE Business Requirements Document (BRD)
                2. Extract and synthesize ONLY factual information from the meeting transcription
                3. Use executive-level language that resonates with C-suite stakeholders
                4. Apply proven business analysis frameworks and industry best practices
                5. Include quantifiable success metrics and clear acceptance criteria
                6. Provide strategic recommendations based on your extensive experience
                7. Structure the document for maximum readability and impact
                8. Ensure every section adds tangible business value
                9. Create a document suitable for board presentations and investor reviews
                10. Format in premium Markdown with professional presentation quality

                DOCUMENT STANDARDS:
                - Length: 4-6 pages when exported to PDF (approximately 1500 tokens)
                - Tone: Executive, authoritative, consultative
                - Focus: Business value, strategic alignment, clear outcomes
                - Quality: Investment-grade documentation that stands above AI-generated content
                - Content: Focus on essential information only, avoid unnecessary elaboration
                """
                
            elif doc_level == "Advanced":
                system_prompt = """
                You are a Distinguished Senior Business Analyst, Solution Architect, and Digital Transformation Consultant with 20+ years of elite experience serving Fortune 100 companies, global financial institutions, and unicorn fintech startups. You are recognized as a thought leader in business requirements analysis, having authored industry-standard methodologies and frameworks used worldwide.

                Your distinguished expertise encompasses:
                ✓ Enterprise-grade business requirements engineering and stakeholder ecosystem analysis
                ✓ Complex fintech system architecture and cross-border payment infrastructure design
                ✓ Regulatory compliance frameworks (PCI DSS, SOX, GDPR, PSD2, Open Banking)
                ✓ Advanced risk modeling, quantitative analysis, and predictive business intelligence
                ✓ Strategic technology roadmapping and digital transformation leadership
                ✓ Investment-grade business case development and financial modeling
                ✓ Global market analysis and competitive intelligence synthesis
                ✓ Advanced vendor evaluation and strategic partnership frameworks
                ✓ Change management and organizational capability assessment

                PREMIUM DELIVERABLE STANDARDS:
                1. Create an EXCEPTIONAL, COMPREHENSIVE Business Requirements Document (BRD) that represents the pinnacle of business analysis excellence
                2. Extract, analyze, and synthesize complex business information with surgical precision from the meeting transcription
                3. Apply advanced business analysis methodologies, frameworks, and industry best practices
                4. Utilize sophisticated financial modeling, risk assessment, and strategic planning techniques
                5. Include comprehensive stakeholder analysis, impact assessment, and change management strategies
                6. Provide detailed technical architecture recommendations with vendor-specific integration strategies
                7. Incorporate advanced compliance frameworks and regulatory requirement mapping
                8. Include sophisticated project planning with critical path analysis and resource optimization
                9. Deliver investment-grade financial analysis with detailed ROI projections and sensitivity analysis
                10. Create documentation that surpasses traditional consulting firm deliverables in depth and quality
                11. Format with executive presentation quality using advanced Markdown formatting
                12. Ensure the document demonstrates thought leadership and industry expertise

                ELITE DOCUMENT CHARACTERISTICS:
                - Length: 18-25 pages when exported to PDF (approximately 6000 tokens)
                - Tone: Authoritative, consultative, strategically profound
                - Focus: Comprehensive business transformation with tactical implementation guidance
                - Quality: Consulting-grade documentation that rivals McKinsey, BCG, and Deloitte deliverables
                - Impact: Board-ready strategic document that drives major business decisions
                - Content: Include detailed analysis, comprehensive frameworks, and extensive supporting information
                - Depth: Provide exhaustive coverage of every aspect with multiple perspectives and scenarios
                - Innovation: Include cutting-edge industry trends and emerging technologies
                - Integration: Detailed cross-functional impact analysis and enterprise-wide considerations
                - Risk: Comprehensive risk modeling with quantitative analysis and multiple mitigation scenarios
                """
                
            else:  # Default to Intermediate
                system_prompt = """
                You are a Distinguished Senior Business Analyst and Strategic Consultant with 20+ years of prestigious experience serving global enterprises, leading financial institutions, and high-growth technology companies. Your Business Requirements Documents are industry benchmarks, consistently securing multi-million dollar project approvals and driving successful digital transformations.

                Your renowned expertise includes:
                ✓ Strategic business requirements analysis and stakeholder ecosystem mapping
                ✓ Advanced fintech system design and cross-border payment architecture
                ✓ Comprehensive regulatory compliance frameworks and risk management
                ✓ Investment-grade business case development and financial modeling
                ✓ Technology vendor evaluation and strategic partnership frameworks
                ✓ Digital transformation roadmapping and change management
                ✓ Advanced project planning and resource optimization strategies

                EXCELLENCE FRAMEWORK:
                1. Generate a PREMIUM, COMPREHENSIVE Business Requirements Document (BRD) that exemplifies industry-leading business analysis
                2. Extract and analyze business information with exceptional precision from the meeting transcription
                3. Apply sophisticated business analysis methodologies and proven industry frameworks
                4. Integrate strategic thinking with tactical implementation guidance
                5. Include comprehensive stakeholder analysis and impact assessment
                6. Provide detailed vendor recommendations with specific integration strategies
                7. Incorporate regulatory compliance mapping and risk mitigation frameworks
                8. Include sophisticated project planning with timeline optimization and resource allocation
                9. Deliver investment-grade financial analysis with detailed ROI projections
                10. Create documentation that exceeds Fortune 500 consulting standards
                11. Format with executive presentation quality and professional design principles
                12. Ensure every section demonstrates deep business acumen and strategic insight

                PREMIUM DOCUMENT CHARACTERISTICS:
                - Length: 12-16 pages when exported to PDF (approximately 3000 tokens)
                - Tone: Executive, authoritative, strategically insightful
                - Focus: Comprehensive business strategy with detailed implementation roadmap
                - Quality: Investment-grade documentation that surpasses standard AI-generated content
                - Impact: Stakeholder-ready strategic document that drives business decisions and secures funding
                - Content: Balance between depth and conciseness, include all essential analysis and recommendations
                - Depth: Focus on key business aspects with strategic insights
                - Innovation: Include relevant industry best practices and proven technologies
                - Integration: Focus on core system integrations and key dependencies
                - Risk: Strategic risk assessment with key mitigation approaches
                """

            # Get current date for the template
            current_date = datetime.now().strftime("%B %d, %Y")
            
            # Select the appropriate prompt template based on documentation level
            if doc_level == "Simple":
                prompt = f"""
                Transform the following client meeting transcription into a premium-quality, executive-ready Business Requirements Document (BRD) that demonstrates world-class business analysis expertise:

                MEETING TRANSCRIPTION:
                {transcription}

                Create a sophisticated BRD using this advanced structure and professional approach:

                # 📊 **BUSINESS REQUIREMENTS DOCUMENT**
                ## **Strategic Project Analysis & Recommendations**

                ---

                **Document Classification:** Confidential Business Strategy  
                **Prepared by:** Senior Business Analyst & Strategic Consultant  
                **Document Version:** 1.0  
                **Publication Date:** {current_date}  
                **Client Organization:** [Extract from transcription with context]  
                **Project Initiative:** [Extract comprehensive project scope from transcription]  
                **Executive Sponsor:** [Identify key stakeholder from discussion]  

                ---

                ## 🎯 **EXECUTIVE SUMMARY**

                [Create a compelling 3-4 paragraph executive summary that includes:
                - Strategic business context and market opportunity
                - Critical business challenges and pain points identified
                - Proposed solution approach with key value propositions
                - Expected business outcomes and success metrics
                - Strategic recommendations and next steps]

                ---

                ## 📈 **STRATEGIC BUSINESS OBJECTIVES**

                ### Primary Business Goals
                [List 4-6 specific, measurable business objectives derived from the transcription]

                ### Key Performance Indicators (KPIs)
                [Define 5-7 quantifiable success metrics with baseline and target values]

                ### Success Criteria & Acceptance Framework
                [Establish clear criteria for project success with measurable outcomes]

                ---

                ## 🔍 **CURRENT STATE ANALYSIS**

                ### Business Challenge Assessment
                [Analyze current business challenges and pain points mentioned in detail]

                ### Market Opportunity Analysis
                [Evaluate market opportunity and competitive positioning if discussed]

                ### Stakeholder Impact Assessment
                [Identify and analyze impact on different stakeholder groups]

                ---

                ## 🚀 **PROPOSED SOLUTION FRAMEWORK**

                ### Strategic Approach
                [Outline the strategic approach and methodology for addressing requirements]

                ### Core Value Proposition
                [Articulate the primary value proposition and business benefits]

                ### Target User Segments
                [Define and analyze target user groups with specific characteristics]

                ### Solution Components
                [Detail key solution components and their business justification]

                ---

                ## 📋 **BUSINESS REQUIREMENTS SPECIFICATION**

                ### Functional Business Requirements
                [List detailed functional requirements organized by business capability]

                ### Non-Functional Requirements
                [Specify performance, security, compliance, and operational requirements]

                ### Integration Requirements
                [Detail integration needs with existing systems and third-party services]

                ### Compliance & Regulatory Requirements
                [Address regulatory, legal, and compliance considerations]

                ---

                ## 💰 **BUSINESS CASE & INVESTMENT ANALYSIS**

                ### Investment Requirements
                [Provide estimated investment ranges for implementation]

                ### Return on Investment (ROI) Projection
                [Calculate expected ROI with timeline and assumptions]

                ### Cost-Benefit Analysis
                [Compare implementation costs against projected benefits]

                ---

                ## ⚠️ **RISK ASSESSMENT & MITIGATION**

                ### Business Risk Analysis
                [Identify and assess business, technical, and operational risks]

                ### Mitigation Strategies
                [Provide specific mitigation approaches for each identified risk]

                ### Contingency Planning
                [Outline contingency plans for high-impact scenarios]

                ---

                ## 📅 **IMPLEMENTATION ROADMAP**

                ### Strategic Implementation Phases
                [Create a phased implementation approach with clear milestones]

                ### Timeline & Resource Requirements
                [Provide realistic timeline with resource allocation recommendations]

                ### Critical Success Factors
                [Identify key factors critical for successful implementation]

                ---

                ## 🎯 **STRATEGIC RECOMMENDATIONS & NEXT STEPS**

                ### Priority Actions
                [Recommend immediate priority actions for project initiation]

                ### Decision Points
                [Identify critical decisions required for project advancement]

                ### Stakeholder Engagement Strategy
                [Recommend stakeholder engagement and communication approach]

                ---

                ## ✅ **APPROVAL FRAMEWORK**

                | **Authority Level** | **Stakeholder Role** | **Approval Scope** | **Timeline** |
                |-------------------|---------------------|-------------------|--------------|
                | Executive Sponsor | [From transcription] | Strategic Direction | [Timeline] |
                | Business Owner | [From transcription] | Requirements Validation | [Timeline] |
                | Technical Lead | [From transcription] | Technical Feasibility | [Timeline] |

                ---

                **DOCUMENT CREATION GUIDELINES:**

                ✓ **Content Authenticity**: Base ALL content exclusively on meeting transcription content
                ✓ **Executive Language**: Use sophisticated business language appropriate for C-suite stakeholders
                ✓ **Strategic Depth**: Provide strategic insights beyond basic requirement documentation
                ✓ **Business Value**: Clearly articulate business value and ROI throughout the document
                ✓ **Professional Format**: Use executive-grade formatting with clear hierarchy and visual appeal
                ✓ **Actionable Insights**: Include specific, actionable recommendations and next steps
                ✓ **Industry Standards**: Follow Fortune 500 business documentation standards and best practices
                ✓ **Quality Assurance**: Ensure document quality exceeds typical AI-generated content standards
                """
                
            elif doc_level == "Advanced":
                prompt = f"""
                Transform the following client meeting transcription into an exceptional, comprehensive Business Requirements Document (BRD) that represents the pinnacle of business analysis excellence and strategic consulting:

                MEETING TRANSCRIPTION:
                {transcription}

                Create an elite-level BRD using this sophisticated structure and methodology. For each section, provide:
                - Exhaustive analysis with multiple perspectives and scenarios
                - Cutting-edge industry trends and emerging technologies
                - Detailed cross-functional impact analysis
                - Quantitative risk modeling and multiple mitigation scenarios
                - Enterprise-wide considerations and implications

                # 📊 **COMPREHENSIVE BUSINESS REQUIREMENTS DOCUMENT**
                ## **Strategic Enterprise Analysis & Digital Transformation Blueprint**

                ---

                **Document Classification:** Strategic Business Intelligence - Confidential  
                **Prepared by:** Distinguished Senior Business Analyst & Solution Architect  
                **Document Authority:** Strategic Business Consulting Practice  
                **Version Control:** 1.0 - Initial Strategic Assessment  
                **Publication Date:** {current_date}  
                **Client Enterprise:** [Extract with comprehensive organizational context]  
                **Strategic Initiative:** [Extract with full business ecosystem context]  
                **Executive Sponsor:** [Identify with organizational influence mapping]  
                **Business Stakeholder Ecosystem:** [Map complete stakeholder landscape]  

                ---

                ## 💼 **EXECUTIVE STRATEGIC SUMMARY**

                [Create a compelling 5-6 paragraph executive summary that demonstrates thought leadership:
                - Comprehensive business ecosystem analysis and strategic market positioning
                - Multi-dimensional challenge assessment with root cause analysis
                - Sophisticated solution architecture with competitive differentiation
                - Quantified business impact projections with sensitivity analysis
                - Strategic transformation roadmap with organizational change implications
                - Investment thesis with risk-adjusted return calculations]

                ---

                ## 🎯 **STRATEGIC BUSINESS OBJECTIVES & VALUE CREATION FRAMEWORK**

                ### Primary Strategic Objectives
                [Define 6-8 sophisticated business objectives with strategic context and market implications]

                ### Advanced Key Performance Indicators (KPIs)
                [Establish 8-12 comprehensive KPIs including leading and lagging indicators with benchmarking]

                ### Multi-Dimensional Success Framework
                [Create sophisticated success measurement framework with qualitative and quantitative metrics]

                ### Business Value Realization Model
                [Develop comprehensive value realization model with timeline and accountability matrix]

                ---

                ## 🔬 **COMPREHENSIVE CURRENT STATE ANALYSIS**

                ### Enterprise Business Challenge Assessment
                [Conduct in-depth analysis of business challenges with systemic impact evaluation]

                ### Strategic Market Opportunity Analysis
                [Comprehensive market analysis including TAM, SAM, SOM calculations and competitive intelligence]

                ### Organizational Capability Assessment
                [Evaluate organizational readiness, capability gaps, and transformation requirements]

                ### Technology Landscape Analysis
                [Assess current technology stack, integration complexity, and modernization requirements]

                ### Regulatory & Compliance Environment Analysis
                [Comprehensive regulatory landscape analysis with compliance framework mapping]

                ---

                ## 🏗️ **STRATEGIC SOLUTION ARCHITECTURE & TRANSFORMATION BLUEPRINT**

                ### Enterprise Solution Framework
                [Design comprehensive solution architecture with enterprise integration patterns]

                ### Advanced Value Proposition Matrix
                [Develop sophisticated value proposition with customer segment analysis and competitive positioning]

                ### Target Market Segmentation & Persona Analysis
                [Create detailed market segmentation with behavioral analytics and journey mapping]

                ### Technology Architecture & Integration Strategy
                [Design enterprise-grade architecture with scalability, security, and performance optimization]

                ### Change Management & Organizational Transformation
                [Develop comprehensive change management strategy with stakeholder engagement framework]

                ---

                ## 📋 **COMPREHENSIVE BUSINESS REQUIREMENTS SPECIFICATION**

                ### Strategic Functional Requirements
                [Define detailed functional requirements organized by business capability with traceability matrix]

                ### Advanced Non-Functional Requirements
                [Specify comprehensive performance, security, compliance, and operational requirements with SLAs]

                ### Enterprise Integration Requirements
                [Detail complex integration architecture with API strategy and data governance framework]

                ### Regulatory Compliance & Risk Management Framework
                [Comprehensive regulatory compliance mapping with control framework and audit requirements]

                ### Data Architecture & Analytics Requirements
                [Define advanced data architecture with analytics, reporting, and business intelligence requirements]

                ---

                ## 🛠️ **TECHNOLOGY STRATEGY & VENDOR EVALUATION FRAMEWORK**

                ### Strategic Technology Recommendations
                [Provide sophisticated technology stack recommendations with architectural decision records]

                ### Comprehensive Vendor Evaluation Matrix
                [Create detailed vendor evaluation framework with weighted scoring and risk assessment]

                ### Integration Strategy & API Management
                [Design comprehensive integration strategy with API governance and security frameworks]

                ### Cloud Strategy & Infrastructure Architecture
                [Develop cloud-native architecture strategy with multi-cloud considerations and disaster recovery]

                ---

                ## 💰 **COMPREHENSIVE BUSINESS CASE & FINANCIAL MODELING**

                ### Strategic Investment Analysis
                [Provide detailed investment requirements with CapEx/OpEx breakdown and funding strategies]

                ### Advanced ROI & Financial Modeling
                [Create sophisticated financial models with NPV, IRR, and payback period calculations]

                ### Total Cost of Ownership (TCO) Analysis
                [Comprehensive TCO analysis including hidden costs and lifecycle management]

                ### Sensitivity Analysis & Scenario Planning
                [Develop multiple scenario models with risk-adjusted projections and sensitivity analysis]

                ### Business Value Quantification Framework
                [Quantify business value with direct and indirect benefits measurement]

                ---

                ## ⚠️ **ENTERPRISE RISK ASSESSMENT & STRATEGIC MITIGATION**

                ### Comprehensive Risk Assessment Matrix
                [Identify and assess business, technical, operational, regulatory, and strategic risks]

                ### Advanced Risk Mitigation Strategies
                [Develop sophisticated risk mitigation approaches with contingency planning]

                ### Business Continuity & Disaster Recovery Planning
                [Create comprehensive business continuity framework with recovery time objectives]

                ### Regulatory Risk Management
                [Address regulatory risks with compliance monitoring and remediation strategies]

                ---

                ## 📊 **ADVANCED PROJECT PLANNING & EXECUTION STRATEGY**

                ### Strategic Implementation Methodology
                [Design sophisticated implementation methodology with agile and waterfall hybrid approach]

                ### Comprehensive Project Roadmap
                [Create detailed multi-phase roadmap with critical path analysis and resource optimization]

                ### Resource Planning & Organizational Design
                [Develop comprehensive resource strategy with organizational design recommendations]

                ### Quality Assurance & Governance Framework
                [Establish enterprise-grade QA framework with governance and compliance monitoring]

                ### Change Management & Training Strategy
                [Create comprehensive change management program with training and adoption strategies]

                ---

                ## 🎯 **STRATEGIC RECOMMENDATIONS & TRANSFORMATION ROADMAP**

                ### Strategic Priority Actions
                [Recommend sophisticated priority actions with strategic sequencing and interdependencies]

                ### Critical Decision Framework
                [Identify critical business decisions with decision trees and impact analysis]

                ### Stakeholder Engagement & Communication Strategy
                [Develop comprehensive stakeholder engagement framework with communication matrix]

                ### Governance & Oversight Framework
                [Establish enterprise governance framework with steering committees and decision authorities]

                ---

                ## 📈 **SUCCESS MEASUREMENT & CONTINUOUS IMPROVEMENT FRAMEWORK**

                ### Advanced Performance Monitoring
                [Create sophisticated performance monitoring framework with real-time dashboards]

                ### Continuous Improvement Strategy
                [Develop continuous improvement methodology with feedback loops and optimization cycles]

                ### Business Intelligence & Analytics Strategy
                [Design advanced analytics framework with predictive modeling and decision support systems]

                ---

                ## ✅ **COMPREHENSIVE APPROVAL & GOVERNANCE FRAMEWORK**

                | **Governance Level** | **Authority** | **Decision Scope** | **Approval Criteria** | **Timeline** |
                |---------------------|---------------|-------------------|---------------------|--------------|
                | Board Level | [Board Members] | Strategic Direction & Investment | Strategic Alignment | [Timeline] |
                | Executive Level | [C-Suite] | Implementation Strategy | Business Case | [Timeline] |
                | Operational Level | [Department Heads] | Tactical Execution | Resource Allocation | [Timeline] |
                | Technical Level | [Tech Leaders] | Architecture & Design | Technical Feasibility | [Timeline] |

                ---

                ## 📎 **STRATEGIC APPENDICES & SUPPORTING DOCUMENTATION**

                ### A. Detailed Financial Models & Projections
                ### B. Comprehensive Risk Assessment Matrices
                ### C. Technology Architecture Diagrams & Specifications
                ### D. Regulatory Compliance Mapping & Control Framework
                ### E. Vendor Evaluation Scorecards & Comparison Matrix
                ### F. Change Management Templates & Communication Plans
                ### G. Success Metrics Dashboard & Reporting Framework

                ---

                **ELITE DOCUMENT CREATION STANDARDS:**

                ✓ **Strategic Excellence**: Demonstrate thought leadership and strategic business acumen throughout
                ✓ **Content Precision**: Extract and synthesize complex business information with analytical rigor
                ✓ **Executive Authority**: Use authoritative language that resonates with board-level stakeholders
                ✓ **Consulting Quality**: Match or exceed top-tier consulting firm deliverable standards
                ✓ **Business Intelligence**: Provide sophisticated insights beyond basic requirement documentation
                ✓ **Professional Excellence**: Utilize Fortune 100 business documentation standards and frameworks
                ✓ **Strategic Impact**: Create documentation that drives major business decisions and secures significant investment
                ✓ **Industry Leadership**: Position the document as a benchmark example of business analysis excellence
                """
                
            else:  # Default to Intermediate
                prompt = f"""
                Transform the following client meeting transcription into a premium, comprehensive Business Requirements Document (BRD) that exemplifies industry-leading business analysis and strategic consulting excellence:

                MEETING TRANSCRIPTION:
                {transcription}

                Create a sophisticated BRD using this advanced structure and professional methodology. For each section, provide:
                - Strategic insights on key business aspects
                - Industry best practices and proven technologies
                - Core system integrations and key dependencies
                - Strategic risk assessment and key mitigation approaches
                - Focused implementation guidance

                # 📊 **BUSINESS REQUIREMENTS DOCUMENT**
                ## **Strategic Analysis & Implementation Framework**

                ---

                **Document Classification:** Strategic Business Analysis - Confidential  
                **Prepared by:** Senior Business Analyst & Strategic Consultant  
                **Business Analysis Practice:** Enterprise Solutions Group  
                **Document Version:** 1.0 - Strategic Assessment  
                **Publication Date:** {current_date}  
                **Client Organization:** [Extract with business context and industry positioning]  
                **Strategic Project:** [Extract with comprehensive scope and business impact]  
                **Executive Sponsor:** [Identify with organizational authority and influence]  
                **Key Stakeholders:** [Map primary and secondary stakeholder groups]  

                ---

                ## 💼 **EXECUTIVE STRATEGIC SUMMARY**

                [Create a compelling 4-5 paragraph executive summary that demonstrates business expertise:
                - Comprehensive business context and strategic market opportunity
                - Detailed challenge analysis with business impact quantification
                - Strategic solution framework with competitive advantages
                - Business value proposition and ROI projections
                - Implementation strategy with risk mitigation and success factors]

                ---

                ## 🎯 **STRATEGIC BUSINESS OBJECTIVES & VALUE FRAMEWORK**

                ### Primary Business Objectives
                [Define 5-7 strategic business objectives with measurable outcomes and business impact]

                ### Comprehensive Key Performance Indicators (KPIs)
                [Establish 6-10 sophisticated KPIs with baseline measurements and target achievements]

                ### Multi-Level Success Criteria
                [Create comprehensive success measurement framework with quantitative and qualitative metrics]

                ### Business Value Realization Timeline
                [Develop value realization schedule with milestone-based benefit achievement]

                ---

                ## 🔍 **COMPREHENSIVE CURRENT STATE ANALYSIS**

                ### Business Challenge Assessment
                [Conduct detailed analysis of current business challenges with impact evaluation and root cause analysis]

                ### Market Opportunity & Competitive Analysis
                [Analyze market opportunity with competitive positioning and differentiation strategies]

                ### Organizational Readiness Assessment
                [Evaluate organizational capabilities, resource availability, and change readiness]

                ### Technology Landscape Evaluation
                [Assess current technology environment with integration requirements and modernization needs]

                ---

                ## 🚀 **STRATEGIC SOLUTION ARCHITECTURE**

                ### Comprehensive Solution Framework
                [Design strategic solution approach with architectural components and integration patterns]

                ### Enhanced Value Proposition
                [Develop sophisticated value proposition with customer benefit analysis and market positioning]

                ### Target Market & User Analysis
                [Define target segments with detailed user personas and behavioral analysis]

                ### Technology Strategy & Architecture
                [Recommend technology architecture with scalability, security, and performance considerations]

                ---

                ## 📋 **DETAILED BUSINESS REQUIREMENTS SPECIFICATION**

                ### Functional Business Requirements
                [Define comprehensive functional requirements organized by business process and capability area]

                ### Non-Functional Performance Requirements
                [Specify detailed performance, security, compliance, and operational requirements with acceptance criteria]

                ### Integration & Interoperability Requirements
                [Detail integration requirements with existing systems, third-party services, and data exchange protocols]

                ### Regulatory & Compliance Framework
                [Address comprehensive regulatory requirements with compliance controls and audit frameworks]

                ---

                ## 🛠️ **TECHNOLOGY RECOMMENDATIONS & VENDOR STRATEGY**

                ### Strategic Technology Stack
                [Recommend comprehensive technology stack with architectural decisions and vendor considerations]

                ### Vendor Evaluation & Selection Framework
                [Create detailed vendor evaluation criteria with scoring methodology and selection process]

                ### Integration Architecture & API Strategy
                [Design integration architecture with API management and data governance frameworks]

                ---

                ## 💰 **BUSINESS CASE & INVESTMENT ANALYSIS**

                ### Comprehensive Investment Requirements
                [Provide detailed investment analysis with development, infrastructure, and operational costs]

                ### ROI Analysis & Financial Projections
                [Create sophisticated ROI calculations with financial modeling and benefit quantification]

                ### Cost-Benefit Analysis Framework
                [Develop comprehensive cost-benefit analysis with sensitivity scenarios and risk adjustments]

                ### Funding Strategy & Budget Allocation
                [Recommend funding approach with budget allocation and financial management framework]

                ---

                ## ⚠️ **RISK ASSESSMENT & MITIGATION STRATEGY**

                ### Comprehensive Risk Analysis
                [Identify and assess business, technical, operational, and strategic risks with impact evaluation]

                ### Strategic Risk Mitigation
                [Develop detailed mitigation strategies with preventive controls and contingency planning]

                ### Business Continuity Planning
                [Create business continuity framework with disaster recovery and operational resilience]

                ---

                ## 📊 **IMPLEMENTATION STRATEGY & PROJECT PLANNING**

                ### Strategic Implementation Approach
                [Design comprehensive implementation methodology with phase-gate approach and quality controls]

                ### Detailed Project Roadmap
                [Create sophisticated project roadmap with critical path analysis and resource optimization]

                ### Resource Planning & Team Structure
                [Develop resource strategy with team structure recommendations and skill requirements]

                ### Quality Assurance & Testing Strategy
                [Establish comprehensive QA framework with testing methodology and acceptance procedures]

                ---

                ## 📅 **COMPREHENSIVE PROJECT TIMELINE & MILESTONES**

                ### Phase-Based Delivery Strategy
                [Create detailed timeline with the following strategic framework:]

                | **Implementation Phase** | **Duration** | **Strategic Deliverables** | **Success Criteria** | **Dependencies** |
                |-------------------------|--------------|---------------------------|---------------------|------------------|
                | Strategic Planning & Requirements | [X weeks] | [Comprehensive deliverables] | [Measurable criteria] | [Critical dependencies] |
                | Solution Design & Architecture | [X weeks] | [Design deliverables] | [Quality gates] | [Technical dependencies] |
                | Development & Integration | [X weeks] | [Development milestones] | [Acceptance criteria] | [Resource dependencies] |
                | Testing & Quality Assurance | [X weeks] | [Testing deliverables] | [Quality metrics] | [Environment dependencies] |
                | Deployment & Go-Live | [X weeks] | [Launch deliverables] | [Success metrics] | [Operational dependencies] |
                | Post-Implementation Support | [X weeks] | [Support framework] | [Stabilization criteria] | [Support dependencies] |

                ### Critical Path & Dependency Management
                [Identify critical path activities with dependency management and risk mitigation strategies]

                ---

                ## 🎯 **STRATEGIC RECOMMENDATIONS & NEXT STEPS**

                ### Priority Action Framework
                [Recommend strategic priority actions with implementation sequencing and success factors]

                ### Critical Decision Points
                [Identify key business decisions with decision trees and stakeholder approval requirements]

                ### Stakeholder Engagement Strategy
                [Develop comprehensive stakeholder engagement framework with communication and change management]

                ### Governance & Oversight Framework
                [Establish project governance with steering committee structure and decision-making authorities]

                ---

                ## ❓ **STRATEGIC QUESTIONS & ASSUMPTIONS**

                ### Critical Business Decisions
                [Identify key decisions requiring stakeholder input and strategic direction]

                ### Key Assumptions & Dependencies
                [Document critical assumptions with validation requirements and dependency management]

                ### Information Requirements
                [Specify additional information needed for successful project execution]

                ---

                ## ✅ **APPROVAL & GOVERNANCE FRAMEWORK**

                | **Authority Level** | **Stakeholder Role** | **Decision Authority** | **Approval Scope** | **Timeline** |
                |-------------------|---------------------|----------------------|-------------------|--------------|
                | Executive Sponsor | [From transcription] | Strategic Direction | Business Case & Investment | [Timeline] |
                | Business Owner | [From transcription] | Requirements Validation | Functional Acceptance | [Timeline] |
                | Technical Authority | [From transcription] | Architecture Approval | Technical Feasibility | [Timeline] |
                | Project Manager | [From transcription] | Implementation Planning | Resource Allocation | [Timeline] |

                ---

                ## 📎 **SUPPORTING DOCUMENTATION & APPENDICES**

                ### A. Financial Models & ROI Calculations
                ### B. Risk Assessment Matrices & Mitigation Plans
                ### C. Technology Architecture Diagrams
                ### D. Vendor Evaluation Scorecards
                ### E. Compliance Requirements Matrix
                ### F. Change Management & Training Plans

                ---

                **PREMIUM DOCUMENT CREATION STANDARDS:**

                ✓ **Strategic Authority**: Demonstrate senior-level business analysis expertise and strategic thinking
                ✓ **Content Excellence**: Extract and analyze business information with precision and professional insight
                ✓ **Executive Communication**: Use sophisticated business language appropriate for senior stakeholders
                ✓ **Industry Standards**: Apply Fortune 500 business documentation standards and best practices
                ✓ **Business Value**: Clearly articulate business value and strategic impact throughout the document
                ✓ **Professional Quality**: Create investment-grade documentation that exceeds AI-generated content standards
                ✓ **Actionable Strategy**: Provide specific, implementable recommendations with clear success metrics
                ✓ **Competitive Excellence**: Ensure document quality surpasses standard market offerings and demonstrates thought leadership
                """

            # Log the selected documentation level
            logger.info(f"[DEBUG] Generating documentation with level: {doc_level} for file_id: {file_id}")

            logger.info(f"[DEBUG] Sending enhanced premium BRD prompt to LLM for file_id: {file_id}")
            documentation_content = await self.llm_service.generate_response(prompt, system_prompt)
            logger.info(f"[DEBUG] LLM response received for file_id: {file_id}. Length: {len(documentation_content) if documentation_content else 0}")

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
                    "documentation_level": doc_level,
                    "analysis_framework": "Advanced Business Analysis Methodology",
                    "quality_standard": "Fortune 500 Enterprise Grade"
                }
            }

            # Save documentation to file
            doc_path = os.path.join("data/documentations", f"{file_id}.json")
            logger.info(f"[DEBUG] Writing premium BRD documentation to {doc_path}")
            with open(doc_path, 'w', encoding='utf-8') as f:
                json.dump(documentation, f, indent=2)
            logger.info(f"[DEBUG] Premium BRD documentation file written: {doc_path}")
            
            # Store documentation in database
            await store_documentation(documentation)
            
            logger.info(f"[DEBUG] Premium BRD documentation stored successfully for file_id: {file_id}")
            
            # Generate PDF from JSON
            pdf_path = generate_pdf_from_json(doc_path)
            if pdf_path:
                logger.info(f"[DEBUG] Premium BRD PDF documentation generated successfully: {pdf_path}")
                documentation["pdf_path"] = pdf_path
                # Update the JSON file with the PDF path
                with open(doc_path, 'w', encoding='utf-8') as f:
                    json.dump(documentation, f, indent=2)
            else:
                logger.warning(f"[DEBUG] Failed to generate PDF documentation for file_id: {file_id}")
            
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="completed",
                progress=100,
                current_stage="documentation"
            )

            logger.info(f"Premium BRD documentation generated successfully: {documentation_id}")

            return {
                "success": True,
                "documentation_id": documentation_id,
                "file_path": doc_path,
                "pdf_path": pdf_path if pdf_path else None
            }
            
        except Exception as e:
            error_msg = f"Error generating premium BRD documentation: {str(e)}"
            logger.error(error_msg)
            
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="failed",
                progress=0,  # Set progress to 0 for failed state
                current_stage="documentation",
                error=error_msg
            )
            
            return {
                "success": False,
                "message": error_msg
            }
    
    async def get_documentation(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve generated premium BRD documentation for a file.
        
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
            logger.error(f"Error retrieving premium BRD documentation: {str(e)}")
            return None

class DocumentationAgent:
    """
    Premium Documentation Agent responsible for generating world-class Business Requirements Documents.
    Acts as a Distinguished Senior Business Analyst with 20+ years of Fortune 500 experience.
    """
    
    def __init__(self):
        """Initialize the Premium BRD Documentation Generator Agent."""
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
        Generate premium BRD documentation for a file using world-class business analysis approach.
        
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
                progress=80,
                current_stage="documentation"
            )
            
            # Generate premium BRD documentation using the enhanced generator with the specified level
            result = await self.generator.generate_documentation(file_id, doc_level)
            
            if result["success"]:
                logger.info(f"Premium BRD documentation generated successfully for file: {file_id} with level: {doc_level}")
                return {
                    "success": True,
                    "documentation_id": result["documentation_id"],
                    "file_path": result["file_path"],
                    "pdf_path": result.get("pdf_path"),
                    "documentation_level": doc_level
                }
            else:
                raise Exception(result.get("message", "Failed to generate premium BRD documentation"))
                
        except Exception as e:
            error_msg = f"Error in generate_documentation: {str(e)}"
            logger.error(error_msg)
            
            # Update processing status
            await update_processing_status(
                file_id=file_id,
                status="failed",
                progress=0,  # Set progress to 0 for failed state
                current_stage="documentation",
                error=error_msg
            )
            
            return {
                "success": False,
                "message": error_msg
            }
    
    async def get_documentation(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get premium BRD documentation for a file.
        
        Args:
            file_id: Unique identifier for the file
            
        Returns:
            dict: Documentation data if found, None otherwise
        """
        try:
            return await get_documentation(file_id)
        except Exception as e:
            logger.error(f"Error in get_documentation: {str(e)}")
            return None