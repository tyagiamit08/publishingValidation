import os
import logging
import asyncio
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