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
    save_state_to_file,
    get_assistants_for_client,
    send_email_with_doc_attached,
    read_email_template
    )
from src.document_processor import extract_images_from_pdf, extract_images_from_docx
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
        
        # Use the proper state update pattern
        state_dict = state.model_dump()
        state_dict["document_content"] = document_content
        state_dict["document_path"] = document_path
        state_dict["document_name"] = file_name
        state_dict["document_bytes"] = file_bytes
        # return State(**state_dict)
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
        logging.info("Identifying clients in document")

        result = await Runner.run(
            clients_identification_agent,
            state.document_content
        )
        client_names = [client.name for client in result.final_output.clients]
        save_state_to_file(client_names, "clients_Identified.txt")

        # Use the proper state update pattern
        # state_dict = state.model_dump()
        # state_dict["clients"] = client_names
        # return State(**state_dict)
        return {"clients": client_names}
    except Exception as e:
        logging.error(f"Error in client identification: {str(e)}", exc_info=True)
        return state

def client_verifier(state: State) -> State:
    """Verify identified clients against a predefined list."""
    logging.info("Verifying identified clients")
    if not state.final_clients:
        return state
    
    verified_clients = []
    # No need to split since final_clients is now a list
    for client in state.final_clients:
        if verify_client(client.strip()):
            verified_clients.append(client)

    save_state_to_file(verified_clients, "verified_clients.txt")
    
    # Create a new state with the verified_clients field updated
    # state_dict = state.model_dump()
    # state_dict["verified_clients"] = verified_clients
    # return State(**state_dict)
    return {"verified_clients": verified_clients}

async def extract_images_node(state: State) -> State:
    file_name = state.document_name.lower()
    file_bytes = state.document_bytes
    
    print ("FileName---->",file_name)

    if file_name.endswith(".pdf"):
        images = extract_images_from_pdf(file_bytes)
    elif file_name.endswith(".docx"):
        images = extract_images_from_docx(file_bytes)
    else:
        raise ValueError("Unsupported file type. Only .pdf and .docx are supported.")
    
    # Use the proper state update pattern
    # state_dict = state.model_dump()
    # state_dict["images"] = images
    # return State(**state_dict)
    return {"images": images}   

async def extract_client_names_node(state: State) -> State:
    """Extract client names from the images."""
    try:
        if not state.images:
            logging.info("Image not found in the uploaded document.")
            return state
        
        logging.info("Extracting Client Names")

        images = state.images
        extracted_names = []

        for img_bytes in images:
            img_b64 = base64.b64encode(img_bytes).decode()

            response = client.chat.completions.create(
                model="gpt-4-turbo",
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
        
        cleaned_names = getCleanNames(extracted_names)
        save_state_to_file(cleaned_names, "clients_Identified_image.txt")
        
        # Use the proper state update pattern
        # state_dict = state.model_dump()
        # state_dict["client_names"] = cleaned_names
        # return State(**state_dict)
        return {"client_names": cleaned_names}  
        
    except Exception as e:
        logging.error(f"Error in client names extraction: {str(e)}", exc_info=True)
        return state
    
async def client_consolidator(state: State) -> State:
    """
    Combine two lists of client names, remove duplicates, and sort them.
    """
    # combined_clients_set = set(state.client_names + state.clients)

    client_names = state.client_names
    clients = state.clients

    sorted_list = list(set(client_names + clients)) #sorted(combined_clients_set)
    
    final_clients_str = ", ".join(sorted_list)        
    save_state_to_file(final_clients_str, "final_clients.txt")
    
    # state_dict = state.model_dump()
    # state_dict["final_clients"] = sorted_list
    # return State(**state_dict)
    return {"final_clients": sorted_list}


async def email_sender_with_doc_attached(state: State) -> State:
    """Send the email with the summary attached."""

    print(f"\n\nExecuting --------email_sender_with_doc_attached\n\n" )
    
    email_sent = False  # Track if any email was successfully sent

    try:
        for client in state.verified_clients:
            assistants= get_assistants_for_client(client)
            if assistants:
                print(f"Assistants for {client}:")
                for assistant in assistants:
                    print(f"- Name: {assistant['name']}, Email: {assistant['email']}")
                    subject, body= read_email_template()
                    formatted_subject = subject.replace("[client_name]", client)
                    formatted_body = body.replace("[recipient_name]", assistant['name'])

                    logging.info(f"---------------Sending email to {assistant['name']} ---------------")

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
        
        # Create a new state with only the email_sent field updated
        # This avoids touching the verified_clients field
        # state_dict = state.model_dump()
        # state_dict["email_sent"] = email_sent
        # return State(**state_dict)

        return {
            "email_sent": email_sent
        }
            
    except Exception as e:
        logging.error(f"Error in email sending: {str(e)}", exc_info=True)
        return state