import logging
from src.models import State
from src.agents import (
    doc_processing_agent,
    clients_identification_agent,
)
import base64
from src.utils import (
    verify_client,
    getCleanNames,
    save_info_in_file,
    get_assistants_for_client,
    send_email_with_doc_attached,
    get_email_template
    )
from src.document_processor import extract_images_from_pdf, extract_images_from_docx
from config import TEXT_TO_IMAGE_IDENTIFICATION_MODEL
from agents import Runner
from openai import OpenAI
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

client = OpenAI()

# # Define the workflow nodes
async def document_processor(state: State,document_path:str,file_name:str) -> State:
    """Process the document and extract its content."""
    try:
        logging.info(f"Processing document: {document_path}")

        with open(document_path, "rb") as f:
            file_bytes = f.read()
    
        result = await Runner.run(
            doc_processing_agent,
            [{"role": "user", "content": document_path}],
        )

        document_content = result.final_output 
        
        return{"document_content": document_content,
                "document_path": document_path,
                "document_name": file_name,
                "document_bytes": file_bytes}
    
    except Exception as e:
        logging.error(f"Error in document processing: {str(e)}", exc_info=True)
        return State(**{**state.model_dump(), "document_content": f"Error: {str(e)}"})

async def client_identifier(state: State) -> State:
    """Identify clients in the document content."""
    try:
        logging.info("Identifying clients in document based on text")

        result = await Runner.run(
            clients_identification_agent,
            state.document_content
        )
        identified_clients = [client.name for client in result.final_output.clients]
        save_info_in_file(identified_clients, "IDENTIFIED CLIENTS FROM DOC TEXT")

        return {"clients_identified": identified_clients}
    except Exception as e:
        logging.error(f"Error in client identification: {str(e)}", exc_info=True)
        return state

def client_verifier(state: State) -> State:
    """Verify identified clients against a predefined list."""
    logging.info("Verifying consolidated clients")
    if not state.consolidated_clients:
        return state
    
    verified_clients = []
    for client in state.consolidated_clients:
        if verify_client(client.strip()):
            verified_clients.append(client)

    save_info_in_file(verified_clients,"VERIFIED CLIENTS BASED ON CUSTOM LIST")
    
    return {"verified_clients": verified_clients}

async def extract_images(state: State) -> State:
    file_name = state.document_name.lower()
    file_bytes = state.document_bytes
    
    if file_name.endswith(".pdf"):
        images = extract_images_from_pdf(file_bytes)
    elif file_name.endswith(".docx"):
        images = extract_images_from_docx(file_bytes)
    else:
        raise ValueError("Unsupported file type. Only .pdf and .docx are supported.")
    
    return {"images": images}   

async def extract_clients(state: State) -> State:
    """Extract client names from the images."""
    try:
        if not state.images:
            logging.info("Image not found in the uploaded document.")
        
        logging.info("Extracting Client Names from document images")

        images = state.images
        extracted_names = []

        for img_bytes in images:
            img_b64 = base64.b64encode(img_bytes).decode()

            response = client.chat.completions.create(
                model=TEXT_TO_IMAGE_IDENTIFICATION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", 
                             "text":
                             """You are an expert in extracting client-related names from images. Your task is to analyze the provided image base64 string and identify all client-related names, such as:
                                - Company names
                                - Business entities
                                - Organizations

                                Guidelines for Extraction:
                                - Focus only on client-related names; ignore unrelated text or general information or other unrelated text.
                                - Ensure accuracy and context awareness to differentiate between actual client names and other text.
                                - Consider variations of client names (e.g., "ABC Corp." vs. "ABC Corporation").
                                - Return the extracted names as a Python list of strings, with each name as a separate list item.

                                Example Output:
                                ["Microsoft", "Amazon"]"""
                              },
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                        ]
                    }
                ]
            )
            cleaned_list = re.split(r'\n-?\s*', response.choices[0].message.content.strip())  # handles both "\n" and "\n- " styles
            extracted_names.extend([item for item in cleaned_list if item])  
        
        clients_from_images = getCleanNames(extracted_names)
        save_info_in_file(clients_from_images, "CLIENTS FROM IMAGES USED IN DOCUMENT")
        
        return {"clients_from_images": clients_from_images}  
        
    except Exception as e:
        logging.error(f"Error in client names extraction: {str(e)}", exc_info=True)
        return state
    
async def client_consolidator(state: State) -> State:
    """
    Combine two lists of client names, remove duplicates, and sort them.
    """
    client_from_images = state.clients_from_images
    clients_identified = state.clients_identified

    consolidated_clients = list(set(client_from_images + clients_identified)) #sorted(combined_clients_set)
    
    consolidated_clients_str = ", ".join(consolidated_clients)        
    save_info_in_file(consolidated_clients_str, "CONSOLIDATED CLIENTS")

    return {"consolidated_clients": consolidated_clients}


async def email_sender(state: State) -> State:
    """Send the email with the document attached."""

    email_sent = False  # Track if any email was successfully sent

    try:
        for client in state.verified_clients:
            assistants= get_assistants_for_client(client)
            if assistants:
                print(f"Assistants for {client}:")
                for assistant in assistants:
                    print(f"- Name: {assistant['name']}, Email: {assistant['email']}")
                    subject, body= get_email_template()
                    formatted_subject = subject.replace("[client_name]", client)
                    formatted_body = body.replace("[recipient_name]", assistant['name'])

                    logging.info(f"---------------Sending email to {assistant['name']} ({assistant['email']})---------------")

                    result = send_email_with_doc_attached(assistant['email'],
                                                           formatted_subject,
                                                           formatted_body,
                                                            state.document_path,
                                                            state.document_name,
                                                            state.email_from_alias)
                    
                    if "successfully" in result.lower():
                        email_sent = True
                    
            else:
                print(f"No assistants found for client: {client}")
                logging.info(f"No assistants found for client: {client}")
        
        return {
            "email_sent": email_sent
        }
            
    except Exception as e:
        logging.error(f"Error in email sending: {str(e)}", exc_info=True)
        return state