import os
import logging
import asyncio
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
    
