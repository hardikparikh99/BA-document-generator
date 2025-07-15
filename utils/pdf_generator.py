"""
PDF Generator utility for the CrewAI Multi-Agent Project Documentation System.
This module converts documentation content to PDF format.
"""
import os
import json
import tempfile
from datetime import datetime
import re
import shutil

# Import reportlab components
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

from utils.logger import get_agent_logger

# Setup logger
logger = get_agent_logger("pdf_generator")

def generate_pdf_from_json(json_file_path):
    """
    Generate a PDF file from a JSON documentation file using ReportLab.
    
    Args:
        json_file_path: Path to the JSON documentation file
        
    Returns:
        str: Path to the generated PDF file or None if failed
    """
    try:
        logger.info(f"Generating PDF from JSON file: {json_file_path}")
        
        # Check if file exists
        if not os.path.exists(json_file_path):
            logger.error(f"JSON file not found: {json_file_path}")
            return None
            
        logger.info(f"JSON file exists, proceeding with PDF generation")
            
        # Read JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            doc_data = json.load(f)
            
        # Extract data
        title = doc_data.get('title', 'Company Documentation')
        content = doc_data.get('content', '')
        metadata = doc_data.get('metadata', {})
        file_id = doc_data.get('file_id', 'unknown')
        
        logger.info(f"Extracted data from JSON: title={title}, file_id={file_id}, content length={len(content)}")
        
        # Create PDF directory if it doesn't exist
        pdf_dir = os.path.join("data", "pdf_documentations")
        os.makedirs(pdf_dir, exist_ok=True)
        logger.info(f"PDF directory ensured: {pdf_dir}")
        
        # Create PDF file path
        pdf_file_path = os.path.join(pdf_dir, f"{file_id}.pdf")
        
        # Create a PDF document using ReportLab
        doc = SimpleDocTemplate(pdf_file_path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Add title
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=16,
            spaceAfter=12
        )
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 12))
        
        # Add metadata section
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading1'],
            fontSize=14,
            spaceAfter=10
        )
        normal_style = styles['Normal']
        
        elements.append(Paragraph("Document Information", heading_style))
        elements.append(Spacer(1, 6))
        
        # Add metadata
        if 'created_at' in metadata:
            elements.append(Paragraph(f"Created: {metadata['created_at']}", normal_style))
        if 'file_type' in metadata:
            elements.append(Paragraph(f"File Type: {metadata['file_type']}", normal_style))
        if 'duration' in metadata:
            elements.append(Paragraph(f"Duration: {metadata['duration']} seconds", normal_style))
        if 'language' in metadata:
            elements.append(Paragraph(f"Language: {metadata['language']}", normal_style))
        
        elements.append(Spacer(1, 12))
        
        # Add content section
        elements.append(Paragraph("Documentation Content", heading_style))
        elements.append(Spacer(1, 6))
        
        # Process markdown content for PDF
        # Replace markdown headers with styled paragraphs
        lines = content.split('\n')
        current_paragraph = ""
        
        for line in lines:
            # Handle headers
            if line.startswith('###'):
                if current_paragraph:
                    elements.append(Paragraph(current_paragraph, normal_style))
                    current_paragraph = ""
                heading3_style = ParagraphStyle(
                    'Heading3',
                    parent=styles['Heading3'],
                    fontSize=12,
                    spaceAfter=6
                )
                elements.append(Paragraph(line.replace('###', '').strip(), heading3_style))
            elif line.startswith('##'):
                if current_paragraph:
                    elements.append(Paragraph(current_paragraph, normal_style))
                    current_paragraph = ""
                heading2_style = ParagraphStyle(
                    'Heading2',
                    parent=styles['Heading2'],
                    fontSize=14,
                    spaceAfter=8
                )
                elements.append(Paragraph(line.replace('##', '').strip(), heading2_style))
            elif line.startswith('#'):
                if current_paragraph:
                    elements.append(Paragraph(current_paragraph, normal_style))
                    current_paragraph = ""
                heading1_style = ParagraphStyle(
                    'Heading1',
                    parent=styles['Heading1'],
                    fontSize=16,
                    spaceAfter=10
                )
                elements.append(Paragraph(line.replace('#', '').strip(), heading1_style))
            # Handle bullet points
            elif line.strip().startswith('*') or line.strip().startswith('+'):
                if current_paragraph:
                    elements.append(Paragraph(current_paragraph, normal_style))
                    current_paragraph = ""
                bullet_text = line.strip().lstrip('*').lstrip('+').strip()
                bullet_style = ParagraphStyle(
                    'Bullet',
                    parent=styles['Normal'],
                    leftIndent=20,
                    firstLineIndent=-15
                )
                elements.append(Paragraph(f"• {bullet_text}", bullet_style))
            # Handle empty lines
            elif not line.strip():
                if current_paragraph:
                    elements.append(Paragraph(current_paragraph, normal_style))
                    current_paragraph = ""
                elements.append(Spacer(1, 6))
            # Regular text
            else:
                # Handle bold text
                line_with_bold = line
                if '**' in line:
                    line_with_bold = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                
                if current_paragraph:
                    current_paragraph += " " + line_with_bold
                else:
                    current_paragraph = line_with_bold
        
        # Add any remaining paragraph
        if current_paragraph:
            elements.append(Paragraph(current_paragraph, normal_style))
        
        # Build the PDF
        try:
            logger.info(f"Building PDF document: {pdf_file_path}")
            doc.build(elements)
            logger.info(f"PDF generated successfully: {pdf_file_path}")
        except Exception as pdf_error:
            logger.error(f"Error building PDF: {str(pdf_error)}")
            # Try with a simpler approach if the first attempt fails
            try:
                logger.info("Trying with a simpler PDF generation approach")
                simple_doc = SimpleDocTemplate(pdf_file_path, pagesize=letter)
                simple_elements = [
                    Paragraph("Documentation", title_style),
                    Spacer(1, 12),
                    Paragraph("Please see the JSON documentation for complete content.", normal_style)
                ]
                simple_doc.build(simple_elements)
                logger.info(f"Simple PDF generated successfully: {pdf_file_path}")
            except Exception as simple_error:
                logger.error(f"Error generating simple PDF: {str(simple_error)}")
                raise
        
        return pdf_file_path
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        return None
