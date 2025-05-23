import os
from openai import AsyncOpenAI
from agents import (
    Agent,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from config import (
    DOC_PROCESSING_MODEL,
    CLIENT_IDENTIFICATION_MODEL
)
import logging
from dotenv import load_dotenv
from src.models import ClientIdentificationResult
from src.tools import extract_document_content

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure OpenAI client
client = AsyncOpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
)

set_default_openai_client(client=client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=True)

# Agent instructions
DOC_PROCESSING_INSTRUCTION = """Extract and read all text, metadata, and embedded information from the provided document, 
including tables, images, and annotations, while preserving the document's structure and formatting. 
Do not exclude or miss any important information.
Ensure compatibility with DOC, DOCX, and PDF formats."""

CLIENT_IDENTIFICATION_INSTRUCTION="""
You are a highly skilled Client Identification Agent, specializing in extracting and recognizing client-specific details from the provided document.

Your task is to thoroughly analyze the provided document and accurately identify any references to clients. This includes:
Client Names : Look for mentions of company names, business entities, or individual client references.
Guidelines for Extraction:
 - Maintain accuracy and context awareness to differentiate between actual client references and general mentions.
 - Consider variations of client names (e.g., "ABC Corp." vs. "ABC Corporation").
Format the extracted information clearly and concisely for downstream processing."""

# Define agents
doc_processing_agent = Agent(
    name="Document Processing Agent",
    instructions=DOC_PROCESSING_INSTRUCTION,
    tools=[extract_document_content],
    model=DOC_PROCESSING_MODEL,
    output_type=str,
)

clients_identification_agent = Agent(
    name="Client Identification Agent",
    instructions=CLIENT_IDENTIFICATION_INSTRUCTION,
    model=CLIENT_IDENTIFICATION_MODEL,
    output_type=ClientIdentificationResult,
)