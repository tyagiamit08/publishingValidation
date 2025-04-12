import os
import logging
import re
import ast
from typing import List, Dict
import smtplib
import json
from email.message import EmailMessage
from config import VALID_CLIENTS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def verify_client(client_name: str) -> bool:
    """Checks if a client is valid based on a predefined list."""
    return client_name in VALID_CLIENTS

def get_assistants_for_client(client_name: str) -> List[Dict[str, str]]:
    """
    Retrieve the list of assistants with their name and email for the given client.
    """
    try:
        # Determine the relative path to the data.json file
        data_file = os.path.join(os.path.dirname(__file__), "..", "data.json")

        # Load the JSON data from the file
        with open(data_file, "r") as file:
            data = json.load(file)

        # Search for the client and retrieve assistants
        for client in data.get("clients", []):
            if client.get("name") == client_name:
                return client["dcs"].get("assistants", [])

        # Return an empty list if the client is not found
        return []

    except Exception as e:
        print(f"Error reading data file: {e}")
        return []
    

def getCleanNames(extracted_names: str) -> List[str]:
    """
    Retrieve a list of clean names from the data.json file.
    """
    # Step 1: Combine lines into a single string
    joined = "\n".join(extracted_names)

    # Step 2: Find all Python-style lists inside code blocks or plain text
    matches = re.findall(r'\[.*?\]', joined, re.DOTALL)

    # Step 3: Flatten all lists and extract strings
    all_names = []
    for m in matches:
        try:
            # Safely evaluate the list
            names = ast.literal_eval(m)
            if isinstance(names, list):
                all_names.extend([n.strip('"') for n in names])
        except Exception:
            pass  # skip any non-list matches

    # Step 4: Optional - deduplicate and sort
    cleaned_names = sorted(set(all_names))
    return cleaned_names

def save_state_to_file(state, filename="state_log.txt"):
    """Save the state to a text file."""
    try:
        # Ensure the logs directory exists
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Define the full file path
        file_path = os.path.join(log_dir, filename)
        
        # Write the state to the file
        with open(file_path, "w") as file:  # Open in append mode
            file.write(f"\n\n{'*' * 30} Log {'*' * 30}\n")
            file.write(f"{state}\n")  # Convert state to string
            file.write(f"{'*' * 70}\n")
        
        logging.info(f"State saved to {file_path}")
    except Exception as e:
        logging.error(f"Error saving state to file {filename}: {str(e)}", exc_info=True)

def send_email_with_doc_attached(recipient_email: str, subject: str, body: str, doc_temp_path: str, file_name: str, email_from_alias: str = None) -> str:
    """Sends an email with the provided details and attaches the document in the email."""
    try:
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

def get_email_template():
    """
    Read the email body from the email_template.json file.
    
    Returns:
        str: The email body, subject
    """
    try:
        # Get the path to the email_template.json file
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'email_template.json')
        
        # Open and parse the JSON file
        with open(template_path, 'r') as file:
            template_data = json.load(file)
        
        # Extract the body content
        body = template_data.get('email_content', {}).get('body', '')
        subject = template_data.get('email_content', {}).get('subject', '')
        
        return subject,body
    except Exception as e:
        print(f"Error reading email template: {str(e)}")
        return "Review Document","Dear [Recipient],\n\nPlease review the attached document.\n\nBest regards,"