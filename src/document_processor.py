import os
from docx import Document
import PyPDF2
import logging
from openai import AsyncOpenAI
from agents import Agent, Runner, trace, function_tool
from config import OPENAI_API_BASE, OPENAI_API_KEY, DOC_PROCESSING_MODEL

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize OpenAI client
client = AsyncOpenAI(
    base_url=OPENAI_API_BASE,
    api_key=OPENAI_API_KEY,
)

def process_docx(doc_path):
    """Process a DOCX file and extract its text content."""
    try:
        logging.info(f"Attempting to process DOCX file: {doc_path}")
        doc = Document(doc_path)
        full_text = []
        for para in doc.paragraphs:
            logging.debug(f"Extracted paragraph: {para.text[:50]}...")  # Log the first 50 characters of each paragraph
            full_text.append(para.text)
        logging.info(f"Successfully processed DOCX file: {doc_path}")
        return "\n".join(full_text)
    except Exception as e:
        logging.error(f"Error reading DOCX file: {str(e)}", exc_info=True)
        return f"Error reading DOCX file: {str(e)}"

def process_pdf(doc_path):
    """Process a PDF file and extract its text content."""
    try:
        with open(doc_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            full_text = []
            for page in reader.pages:
                full_text.append(page.extract_text())
            return "\n".join(full_text)
    except Exception as e:
        logging.error(f"Error reading PDF file: {str(e)}", exc_info=True)
        return f"Error reading PDF file: {str(e)}"




