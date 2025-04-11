
import logging
from agents import (
    function_tool,
)
import os
import smtplib
from email.message import EmailMessage
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
    

# @function_tool
def send_email_with_doc_attached(recipient_email: str, subject: str, body: str, doc_temp_path: str, file_name: str, email_from_alias: str = None) -> str:
    """Sends an email with the provided details and attaches the document in the email."""
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

        # Attach the uploaded file
        if doc_temp_path and os.path.exists(doc_temp_path):
            with open(doc_temp_path, "rb") as f:
                file_data = f.read()
                # file_name = os.path.basename(doc_temp_path)
            msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

        # Send the email using SMTP
        with smtplib.SMTP_SSL(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))) as server:
            server.login(os.getenv("EMAIL_SENDER"), os.getenv("EMAIL_PASSWORD"))
            server.send_message(msg)

        logging.info("Email sent successfully!")
        return "Email sent successfully!"
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}", exc_info=True)
        return f"Error sending email: {str(e)}"
