import os
import logging
import asyncio
from langgraph.graph import StateGraph, START, END
from src.models import State, ClientIdentificationResult, EmailDetail
from src.agents import (
    doc_processing_agent,
    clients_identification_agent,
    summarization_agent,
    draft_email_agent,
    send_email_agent
)

from src.utils import verify_client
from agents import Runner
from IPython.display import Image, display

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# # Ensure images directory exists
# os.makedirs("images", exist_ok=True)

# # Define the workflow nodes
async def document_processor(state: State) -> State:
    """Process the document and extract its content."""
    try:
        logging.info(f"Processing document: {state.document_path}")
        result = await Runner.run(
            doc_processing_agent,
            [{"role": "user", "content": state.document_path}],
        )
        return State(**{**state.model_dump(), "document_content": result.final_output})
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
        return State(**{**state.model_dump(), "clients": result.final_output})
    except Exception as e:
        logging.error(f"Error in client identification: {str(e)}", exc_info=True)
        return state

def client_verifier(state: State) -> State:
    """Verify identified clients against a predefined list."""
    logging.info("Verifying identified clients")
    if not state.clients:
        return state
    
    verified_clients = []
    for client in state.clients.clients:
        if verify_client(client.name):
            verified_clients.append(client.name)
    
    return State(**{**state.model_dump(), "verified_clients": verified_clients})

async def document_summarizer(state: State) -> State:
    """Summarize the document content."""
    try:
        logging.info("Summarizing document")
        result = await Runner.run(
            summarization_agent,
            state.document_content
        )
        return State(**{**state.model_dump(), "summary": result.final_output})
    except Exception as e:
        logging.error(f"Error in document summarization: {str(e)}", exc_info=True)
        return state

async def email_drafter(state: State) -> State:
    """Draft an email based on the document summary."""
    try:
        logging.info("Drafting email")
        result = await Runner.run(
            draft_email_agent,
            state.summary
        )
        return State(**{**state.model_dump(), "email_details": result.final_output})
    except Exception as e:
        logging.error(f"Error in email drafting: {str(e)}", exc_info=True)
        return state

async def email_sender(state: State) -> State:
    """Send the email with the summary attached."""
    if not state.email_details:
        return state
    
    try:
        logging.info(f"Sending email to {state.recipient_email}")
        email_input = {
            "recipient_email": state.recipient_email,
            "subject": state.email_details.subject,
            "body": state.email_details.body,
            "summary": state.summary,
            "email_from_alias": state.email_from_alias
        }
        
        result = await Runner.run(
            send_email_agent,
            [
                {
                    "role": "user",
                    "content": f"""
                    Please send an email to {state.recipient_email} with email from alias '{state.email_from_alias}'
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
        
        return State(**{**state.model_dump(), "email_sent": "successfully" in result.final_output.lower()})
    except Exception as e:
        logging.error(f"Error in email sending: {str(e)}", exc_info=True)
        return state

def create_workflow_graph():
    """Create the workflow graph using LangGraph."""
    # Create a new graph
    workflow = StateGraph(State)
    
    # Add nodes
    workflow.add_node("document_processor", document_processor)
    workflow.add_node("client_identifier", client_identifier)
    workflow.add_node("client_verifier", client_verifier)
    workflow.add_node("document_summarizer", document_summarizer)
    # workflow.add_node("email_drafter", email_drafter)
    # workflow.add_node("email_sender", email_sender)

    workflow.add_edge(START,"document_processor")
    workflow.add_edge("document_processor", "client_identifier")
    workflow.add_edge("client_identifier", "client_verifier")
    workflow.add_edge("document_processor", "document_summarizer")
    # workflow.add_edge("document_summarizer", "email_drafter")
    # workflow.add_edge("client_verifier", "email_sender")
    # workflow.add_edge("email_drafter", "email_sender")
    # workflow.add_edge("email_sender",END)
    workflow.add_edge("client_verifier",END)
    workflow.add_edge("document_summarizer",END)
    
    # Set the entry point
    workflow.set_entry_point("document_processor")
    
    return workflow

def visualize_graph():
    """Generate and save a visualization of the workflow graph."""
    try:
        # Create the workflow graph
        workflow = create_workflow_graph()

        # Compile the workflow and generate the graph
        graph = workflow.compile().get_graph(xray=True)

        # Save the graph as a PNG image
        graph_image_path = os.path.abspath("src/images/workflow_graph.png")
        os.makedirs(os.path.dirname(graph_image_path), exist_ok=True)

        # Use LangGraph's draw_mermaid_png method to get the PNG data
        png_data = graph.draw_mermaid_png()

        # Write the PNG data to a file
        with open(graph_image_path, "wb") as f:
            f.write(png_data)

        # Log the absolute path and verify the file exists
        logging.info(f"Workflow graph saved at: {graph_image_path}")
        if os.path.exists(graph_image_path):
            logging.info("Graph image successfully created.")
        else:
            logging.error("Graph image was not created.")

        return graph_image_path
    except AttributeError as e:
        logging.error(f"AttributeError: {str(e)}", exc_info=True)
        raise RuntimeError("Failed to generate workflow graph. Ensure LangGraph is properly installed and configured.") from e
    except Exception as e:
        logging.error(f"Error visualizing graph: {str(e)}", exc_info=True)
        raise RuntimeError("Failed to generate workflow graph.") from e
