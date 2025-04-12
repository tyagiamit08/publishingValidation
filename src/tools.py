
import logging
from agents import (
    function_tool,
)
import os
from dotenv import load_dotenv
from src.document_processor import process_docx,process_pdf

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@function_tool
def extract_document_content(doc_path: str) -> str:
    """Reads the content of a DOC, DOCX, or PDF file."""
    # Ensure the file exists
    if not os.path.isfile(doc_path):
        return f"Error: The file '{doc_path}' does not exist."

    # Process DOCX and PDF files based on their extension
    file_extension = doc_path.split('.')[-1].lower()
    print(f"Processing file with extension: {file_extension}")
    if file_extension == "docx":
        return process_docx(doc_path)
    elif file_extension == "pdf":
        return process_pdf(doc_path)
    else:
        return "Error: Unsupported file format. Please upload a DOCX or PDF file."
    