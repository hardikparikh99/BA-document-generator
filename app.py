"""
Streamlit frontend for the CrewAI Multi-Agent Project Documentation System.
This app allows users to upload media files, process them, and view generated documentation.
"""
import os
import time
import base64
import requests
import streamlit as st
from typing import Dict, Any, Optional, List

# Set Streamlit port
os.environ['STREAMLIT_SERVER_PORT'] = '8501'

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Set page config
st.set_page_config(
    page_title="Business Analyst Documentation Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    .stButton button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-weight: bold;
    }
    .pdf-viewer {
        width: 100%;
        height: 800px;
        border: none;
    }
    .download-btn {
        margin-top: 10px;
        margin-bottom: 10px;
    }
    h1, h2, h3 {
        margin-bottom: 0.5rem;
    }
    .stAlert {
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

# Helper functions
def upload_and_process_file(uploaded_file, doc_type="BRD", doc_level="Intermediate"):
    """Upload a file to the API and start processing."""
    try:
        # Create a files dictionary for the request
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        
        # Log the upload attempt
        st.write(f"Attempting to upload file: {uploaded_file.name} ({uploaded_file.size} bytes)")
        st.write(f"Document type: {doc_type}")
        st.write(f"Documentation level selected: {doc_level}")
        
        # Make the API request with documentation type and level parameters
        response = requests.post(
            f"{API_BASE_URL}/upload", 
            files=files,
            data={
                "doc_type": doc_type,
                "doc_level": doc_level
            }
        )
        
        # Log the response status
        st.write(f"Upload response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            st.write(f"Response content: {result}")
            
            if result.get("success"):
                st.write(f"File ID: {result.get('file_id')}")
                return result
            else:
                st.error(f"Upload failed: {result.get('message', 'Unknown error')}")
                return None
        else:
            st.error(f"Upload failed with status code {response.status_code}")
            try:
                st.write(f"Error details: {response.json()}")
            except:
                st.write("Could not parse error response")
            return None
    except Exception as e:
        st.error(f"Error uploading file: {str(e)}")
        return None

def check_documentation_exists(file_id):
    """Check if documentation exists for the given file ID."""
    try:
        st.write(f"Checking if documentation exists for file ID: {file_id}")
        response = requests.get(f"{API_BASE_URL}/documentation/{file_id}")
        st.write(f"Documentation check status code: {response.status_code}")
        
        if response.status_code == 200:
            st.write("Documentation exists!")
            return True
        else:
            st.write(f"Documentation not ready yet. Status: {response.status_code}")
            # Also check processing status
            try:
                status_response = requests.get(f"{API_BASE_URL}/status/{file_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    st.write(f"Processing status: {status_data.get('status')}")
                    st.write(f"Progress: {status_data.get('progress')}%")
                    st.write(f"Current stage: {status_data.get('current_stage')}")
                    if status_data.get('error'):
                        st.error(f"Processing error: {status_data.get('error')}")
            except Exception as status_err:
                st.write(f"Could not get processing status: {str(status_err)}")
            return False
    except Exception as e:
        st.write(f"Error checking documentation: {str(e)}")
        return False

def get_pdf_content(file_id):
    """Get PDF content for the given file ID."""
    try:
        response = requests.get(f"{API_BASE_URL}/download/{file_id}?format=pdf")
        if response.status_code == 200:
            return response.content
        return None
    except:
        return None

def get_document_download_url(file_id, format="pdf"):
    """Get download URL for the document."""
    return f"{API_BASE_URL}/download/{file_id}?format={format}"

def display_pdf(pdf_content):
    """Display PDF content in an iframe."""
    base64_pdf = base64.b64encode(pdf_content).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" class="pdf-viewer"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def create_download_button(file_id, format, label):
    """Create a download button for the document."""
    download_url = get_document_download_url(file_id, format)
    st.markdown(
        f'<div class="download-btn"><a href="{download_url}" target="_blank">'
        f'<button style="width:100%;padding:0.5em;background-color:#4CAF50;color:white;'
        f'border:none;border-radius:5px;cursor:pointer;">'
        f'{label}</button></a></div>',
        unsafe_allow_html=True
    )

# Main app
st.title("📄 Business Analyst Documentation Generator")
st.markdown("---")

# Sidebar
st.sidebar.title("Document Generator")

# Video upload section
uploaded_file = st.sidebar.file_uploader(
    "Upload a video or audio file",
    type=["mp4", "avi", "mov", "mkv", "mp3", "wav", "m4a", "ogg"],
    help="Upload a media file to generate documentation."
)

# Document type selection
doc_type = st.sidebar.selectbox(
    "Select Document Type",
    options=["BRD", "FRD", "SOW"],
    help="Choose the type of document to generate."
)

# Level selection (Simple/Intermediate/Advanced)
doc_level = st.sidebar.radio(
    "Select Level",
    options=["Simple", "Intermediate", "Advanced"],
    help="Choose the detail level for the document."
)

# Generate Document button
if st.sidebar.button("Generate Document"):
    if uploaded_file is not None:
        with st.spinner("Uploading and generating document..."):
            result = upload_and_process_file(uploaded_file, doc_type, doc_level)
            if result:
                file_id = result.get("file_id")
                st.session_state["current_file_id"] = file_id
                st.session_state["sections"] = None  # Reset sections
                st.success(f"Document generated! File ID: {file_id}")
    else:
        st.sidebar.warning("Please upload a file first.")

# --- Main Bar ---
st.title("📄 Document Sections")

file_id = st.session_state.get("current_file_id")

if not file_id:
    st.info("Upload a file and generate a document to get started.")
else:
    # Fetch and store sections if not already in session state
    if "sections" not in st.session_state or st.session_state["sections"] is None:
        # Simulate fetching sections from backend (replace with real API call)
        # Here, we use placeholder sections for demonstration
        st.session_state["sections"] = [
            {"title": "Executive Summary", "content": "...", "edited": False, "selected": True},
            {"title": "Project Scope and Objectives", "content": "...", "edited": False, "selected": True},
            {"title": "Stakeholder Analysis", "content": "...", "edited": False, "selected": True},
            {"title": "Functional Requirements", "content": "...", "edited": False, "selected": True},
            {"title": "Technical Requirements", "content": "...", "edited": False, "selected": True},
        ]
        st.session_state["new_sections"] = []
        st.session_state["edited_sections"] = set()

    # Display all sections (generated + new)
    st.subheader("Sections")
    all_sections = st.session_state["sections"] + st.session_state.get("new_sections", [])
    for idx, section in enumerate(all_sections):
        col1, col2 = st.columns([0.05, 0.95])
        with col1:
            section["selected"] = st.checkbox("", value=section.get("selected", True), key=f"select_{idx}")
        with col2:
            st.markdown(f"**{section['title']}**")
            # Allow editing only once
            if not section.get("edited", False):
                new_content = st.text_area(f"Edit section: {section['title']}", section["content"], key=f"edit_{idx}")
                if st.button(f"Save Edit: {section['title']}", key=f"save_{idx}"):
                    section["content"] = new_content
                    section["edited"] = True
                    st.session_state["edited_sections"].add(idx)
                    st.success(f"Section '{section['title']}' edited. Further edits disabled.")
            else:
                st.write(section["content"])
                st.info("Editing disabled (one round only).")
        st.markdown("---")

    # Chatbox to add a new section
    st.subheader("Add a New Section")
    new_section_title = st.text_input("Section Title", key="new_section_title")
    new_section_content = st.text_area("Section Content", key="new_section_content")
    if st.button("Add Section"):
        if new_section_title and new_section_content:
            st.session_state["new_sections"].append({
                "title": new_section_title,
                "content": new_section_content,
                "edited": True,  # Already edited
                "selected": True
            })
            st.success(f"Section '{new_section_title}' added.")
            st.session_state["new_section_title"] = ""
            st.session_state["new_section_content"] = ""
        else:
            st.warning("Please provide both a title and content for the new section.")

    # Generate Final Document button
    st.subheader("")
    if st.button("Generate Final Document"):
        # Combine selected sections
        selected_sections = [s for s in st.session_state["sections"] + st.session_state["new_sections"] if s["selected"]]
        st.session_state["final_document"] = selected_sections
        st.success("Final document generated! You can now export as PDF.")

    # Generate PDF button
    if st.session_state.get("final_document"):
        if st.button("Generate PDF"):
            # Here, you would call your backend to generate the PDF from selected sections
            st.info("PDF generation triggered (implement backend call here).")
