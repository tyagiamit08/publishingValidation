from dotenv import load_dotenv
from langgraph.graph import StateGraph
from IPython.display import Image, display
# from helpers import extract_document_content
from openai import AsyncOpenAI
from docx import Document
from pydantic import BaseModel,Field,EmailStr
from typing import List, Optional
import smtplib
from email.message import EmailMessage
import os
from agents import (
    Agent,
    Runner,
    trace,
    function_tool,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# region Setting up Environment

load_dotenv()

BASE_URL = os.getenv("OPENAI_API_BASE")
API_KEY = os.getenv("OPENAI_API_KEY")

client = AsyncOpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)

set_default_openai_client(client=client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=True)

if not BASE_URL or not API_KEY:
    raise ValueError(
        "Please set OPENAI_API_BASE, OPENAI_API_KEY via env var or code."
    )
# endregion

# region Functions to process files
def process_docx(doc_path):
    try:
        doc = Document(doc_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text)
    except Exception as e:
        return f"Error reading DOCX file: {str(e)}"

def process_pdf(doc_path):
    try:
        with open(doc_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            full_text = []
            for page in reader.pages:
                full_text.append(page.extract_text())
            return "\n".join(full_text)
    except Exception as e:
        return f"Error reading PDF file: {str(e)}"
    
@function_tool
def extract_document_content(doc_path: str) -> str:
    """Reads the content of a DOC, DOCX, or PDF file."""
    # Ensure the file exists in the same directory
    if not os.path.isfile(doc_path):
        return f"Error: The file '{doc_path}' does not exist in the current directory."

    # Process DOCX and PDF files based on their extension
    file_extension = doc_path.split('.')[-1].lower()
    if file_extension == "docx":
        return process_docx(doc_path)
    elif file_extension == "pdf":
        return process_pdf(doc_path)
    else:
        return "Error: Unsupported file format. Please upload a DOCX or PDF file."
    
# endregion

# region Agents Instructions

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
Analyze the provided document and generate a detailed yet concise summary that captures all key points, 
main ideas, and critical details. Structure the summary for clarity and readability, 
highlighting important sections such as conclusions, recommendations, or action items. 
Include relevant metadata (e.g., title, author, date) if available. 
Ensure the summary preserves the context and tone of the document while avoiding unnecessary repetition or irrelevant details."""

# endregion

# region Models

class ClientInfo(BaseModel):
    name: str = Field(..., description="The identified client or company name.")

class ClientIdentificationResult(BaseModel):
    clients: List[ClientInfo] = Field(..., description="A list of identified clients with relevant details.")

class EmailDetail(BaseModel):
    subject: str = Field(..., description="The subject of the email.")
    body: str = Field(..., description="The body content of the email.")

# endregion
    
@function_tool
def send_email(recipient_email: str, subject: str, body: str, summary: str, email_from_alias: str = None) -> str:
    """Sends an email with the provided details and attaches the summary."""
    try:
        # Log the email details
        logging.info(f"Attempting to send email to: {recipient_email}")
        logging.info(f"Subject: {subject}")
        logging.info(f"Body: {body}")
        if email_from_alias:
            logging.info(f"Email From Alias: {email_from_alias}")

        # Create the email
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{email_from_alias} <{os.getenv('EMAIL_SENDER')}>" if email_from_alias else os.getenv("EMAIL_SENDER")
        msg["To"] = recipient_email
        msg.set_content(body)

        # Attach the summary as a text file
        msg.add_attachment(summary.encode("utf-8"), maintype="text", subtype="plain", filename="summary.txt")

        # Send the email using SMTP
        with smtplib.SMTP_SSL(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))) as server:
            server.login(os.getenv("EMAIL_SENDER"), os.getenv("EMAIL_PASSWORD"))
            server.send_message(msg)

        logging.info("Email sent successfully!")
        return "Email sent successfully!"
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}", exc_info=True)
        return f"Error sending email: {str(e)}"
    
        
#region AI Agents

doc_processing_agent = Agent(
    name="Document Processing Agent",
    instructions=DOC_PROCESSING_INSTRUCTION,
    tools=[extract_document_content],
    model="gpt-3.5-turbo",
    output_type=str,
)

clients_identification_agent = Agent(
    name="Document Processing Agent",
    instructions=CLIENT_IDENTIFICATION_INSTRUCTION,
    # model="gpt-4.5-preview-2025-02-27", #faster
    model="o1",
    output_type=ClientIdentificationResult,
)

summarization_agent = Agent(
    name="Document Summarization Agent",
    instructions=DOC_SUMMARIZATION_INSTRUCTION,
    model="gpt-4",
    output_type=str,    
)

send_email_agent = Agent(
    name="Send Email Agent",
    instructions="""
        You are an email-sending expert. Your task is to send an email with the provided summary as an attachment.
        Send a professional email to the recipient with the subject and body provided from the context.
        The input will include:
        - recipient_email: The email address of the recipient.
        - subject: The subject of the email.
        - body: The body of the email.
        - summary: The summary content to be attached as a file.
        Save the summary as a text file named 'summary.txt' and attach it to the email.
        Ensure the email is sent successfully using the provided SMTP server details.
    """,
    tools=[send_email],
    model="gpt-4",
    output_type=str,
)

# Agent for drafting the email content
draft_email_agent = Agent(
    name="Email Drafting Agent",
    instructions="""
        You are an expert email drafting agent. Your task is to create a professional and engaging email based on the provided summary.
        The email should include:
        - A clear and concise subject line summarizing the purpose of the email.
        - A well-structured body that includes:
            - A greeting.
            - A brief introduction or context.
            - The key points from the summary.
            - A closing statement with a call to action, if applicable.
        Ensure the tone is professional and appropriate for the recipient. Don't explicitly ask to connect or meet or setup a followup discussion. The email should simply provide the summary and express willingness to discuss further if needed.
    """,
    model="gpt-4.5-preview-2025-02-27",
    output_type=EmailDetail,
)

# endregion

# region Helper Functions

def verify_client(client_name: str) -> bool:
    """Checks if a client is valid based on a predefined list."""
    return client_name in VALID_CLIENTS

VALID_CLIENTS = ["Neste", "IBM", "IKEA", "Microsoft","Unilever"]

def print_client_identification(result: ClientIdentificationResult):
    for idx, client in enumerate(result.clients, start=1):
        print(f"Client {idx}: {client.name}")
        print("\n" + "-"*30 + "\n")





# endregion


async def main():
    # doc_path = os.path.join(os.getcwd(), "AI.docx")
    doc_path = os.path.join(os.getcwd(), "input.docx")
    
    # Ensure the file exists in the same directory
    if not os.path.isfile(doc_path):
        print(f"Error: The file '{doc_path}' does not exist in the current directory.")
        return
    
    with trace("Document Processing Agent Execution"):
        try:
            doc_processing_result = await Runner.run(
                doc_processing_agent,
                [{"role": "user", "content": doc_path}],
            )
            print("----------------------------------Extracted Information:----------------------------------\n\n\n\n")
            print(doc_processing_result.final_output)

            clients_result = await Runner.run(
                clients_identification_agent,doc_processing_result.final_output)

            print("----------------------------------Clients Information:----------------------------------\n\n\n\n")
            print(print_client_identification(clients_result.final_output))

            verified_clients = []
            for client in clients_result.final_output.clients:
                is_verified = verify_client(client.name)
                if(is_verified):
                 verified_clients.append(client.name)
            
            print(f"\n\n----------------------------------Verified Clients:----------------------------------\n\n {verified_clients}")


            summarization_result = await Runner.run(
                summarization_agent,doc_processing_result.final_output)
            
            print("----------------------------------Summarization:----------------------------------\n\n")
            print(summarization_result.final_output)
            
            emailDetail_result = await Runner.run(
                draft_email_agent,summarization_result.final_output)
            
            print("----------------------------------Draft Email Details:----------------------------------\n\n")
            print(emailDetail_result.final_output.subject)
            print(emailDetail_result.final_output.body)

            email_input={
                "recipient_email": "tyagiamitttttt@gmail.com",
                "recipient_name": "Amit Tyagi",
                "subject": emailDetail_result.final_output.subject,
                "body":  emailDetail_result.final_output.body,
                "summary": summarization_result.final_output,
                "email_from_alias" : "AI Agent"
            } 

            email_result = await Runner.run(
                send_email_agent,
                [
                    {
                        "role": "user",
                        "content": f"""
                        Please send an email to {email_input['recipient_name']} with email {email_input['recipient_email']} with email from alias '{email_input['email_from_alias']}'
                        with the subject '{email_input['subject']}', the following body text, 
                        and an attached summary file.

                        Body:
                        {email_input['body']}

                        Summary (to be attached as 'summary.txt'):
                        {email_input['summary']}
                        """,
                    }
                ]
            )
        except Exception as e:
            logging.error("An error occurred during agent execution", exc_info=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())