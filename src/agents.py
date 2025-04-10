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
    CLIENT_IDENTIFICATION_MODEL,
    SUMMARIZATION_MODEL,
    EMAIL_DRAFTING_MODEL,
)
import smtplib
from email.message import EmailMessage
import logging
from dotenv import load_dotenv
from src.models import ClientIdentificationResult,EmailDetail
# from src.tools import send_email, 
from src.tools import extract_document_content,send_email_with_doc_attached

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

DOC_SUMMARIZATION_INSTRUCTION="""You are a summarization expert. 
You need to analyze and then generate a detailed yet concise summary that captures all key points from the provided document, 
main ideas, and critical details. Structure the summary for clarity and readability, 
highlighting important sections such as conclusions, recommendations, or action items. 
Include relevant metadata (e.g., title, author, date) if available. 
Ensure the summary preserves the context and tone of the document while avoiding unnecessary repetition or irrelevant details."""

DRAFT_EMAIL_INSTRUCTIONS="""
        You are an expert email drafting agent. Your task is to create a professional and concise email.
        The email should include:
        - A clear and concise subject line based on the provided content.
        - A well-structured body that includes:
            - A greeting: "Dear [recipient_name]"
            - A brief introduction providing context about the attachment (e.g., "Please find attached the document on the key points").
            - A polite request for feedback or action (e.g., "Kindly review the document and share your feedback or let us know if further clarification is needed.").
            - A closing statement: "Best Regards."
        Ensure the tone is professional, polite, and appropriate for the recipient.
    """

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

summarization_agent = Agent(
    name="Document Summarization Agent",
    instructions=DOC_SUMMARIZATION_INSTRUCTION,
    model=SUMMARIZATION_MODEL,
    output_type=str,    
)

draft_email_agent = Agent(
    name="Email Drafting Agent",
    instructions=DRAFT_EMAIL_INSTRUCTIONS,
    model=EMAIL_DRAFTING_MODEL,
    output_type=EmailDetail,
)

send_email_with_doc_attached_agent = Agent(
    name="Send Email Agent",
    instructions="""
        You are an email-sending expert. Your task is to send an email with an attachment of the uploaded document.
        Send a professional email to the recipient with the subject and body provided from the context.
        The input will include:
        - recipient_email: The email address of the recipient.
        - subject: The subject of the email.
        - body: The body of the email.
        Attach the uploaded doucment to the email.
        Ensure the email is sent successfully using the provided SMTP server details.
    """,
    tools=[send_email_with_doc_attached],
    model="gpt-4",
    output_type=str,
)