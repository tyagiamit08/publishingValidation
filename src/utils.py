import os
import logging
import asyncio
import re
import ast
from typing import List, Dict
from src.models import ClientIdentificationResult

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


VALID_CLIENTS = ["Neste", "IBM", "IKEA", "Microsoft", "Unilever"]

def verify_client(client_name: str) -> bool:
    """Checks if a client is valid based on a predefined list."""
    return client_name in VALID_CLIENTS


def print_client_identification(result: ClientIdentificationResult):
    for idx, client in enumerate(result.clients, start=1):
        print(f"Client {idx}: {client.name}")
        print("\n" + "-"*30 + "\n")


def run_async(coroutine):
    """Run an async function in a synchronous context."""
    return asyncio.run(coroutine)

import json

def get_assistants_for_client(client_name: str) -> List[Dict[str, str]]:
    """
    Retrieve the list of assistants with their name and email for the given client.

    Args:
        client_name (str): The name of the client to search for.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing assistant names and emails.
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

    Returns:
        List[str]: A list of clean names.
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
        with open(file_path, "a") as file:  # Open in append mode
            file.write(f"\n\n{'*' * 30} State Log {'*' * 30}\n")
            file.write(f"{state}\n")  # Convert state to string
            file.write(f"{'*' * 70}\n")
        
        logging.info(f"State saved to {file_path}")
    except Exception as e:
        logging.error(f"Error saving state to file {filename}: {str(e)}", exc_info=True)