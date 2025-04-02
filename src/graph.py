import os
import logging
import asyncio
from langgraph.graph import StateGraph, START, END
from src.models import State, ClientIdentificationResult, EmailDetail,ClientInfo
from src.agents import (
    doc_processing_agent,
    clients_identification_agent,
    summarization_agent,
    draft_email_agent,
    # send_email_agent,
    send_email_with_doc_attached_agent
)

from src.utils import verify_client, get_assistants_for_client
from agents import Runner
from IPython.display import Image, display

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# # Ensure images directory exists
# os.makedirs("images", exist_ok=True)

# # Define the workflow nodes
async def document_processor(state: State,document_path:str,file_name:str) -> State:
    """Process the document and extract its content."""
    try:
        logging.info(f"Processing document: {document_path}")
        result = await Runner.run(
            doc_processing_agent,
            [{"role": "user", "content": document_path}],
        )

        document_content = result.final_output 
        # new_state = state.model_dump()  # Convert to dict
        # new_state["document_content"] = document_content
        # new_state["document_path"] = document_path
        # new_state["document_name"] = file_name
        
        # return State(
        #     document_content=result.final_output,
        #     **{key: getattr(state, key) for key in state.__fields__ if key not in ["document_content"]}
        # )
        # return State(
        #     document_content=document_content
        # )
        print (f"\n\n\n\n ***********************State in Doc Processor ***********************: {state} \n\n\n\n")

        return {"document_content": document_content, "document_path": document_path,"document_name": file_name}
        # return State(**new_state)  
        # return State(**{**state.model_dump(), "document_content": result.final_output})
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
        # Convert result.final_output to a list of strings (extracting the 'name' attribute)
        client_names = [client.name for client in result.final_output.clients]
        
         # Return a new State with only the updated 'clients' field
        # return State(
        #     clients=client_names,
        # )

        print (f"\n\n\n\n ***********************State in Client Identifier ***********************: {state} \n\n\n\n")

        return {"clients": client_names}
        # return State(**{**state.model_dump(), "clients": client_names})
    except Exception as e:
        logging.error(f"Error in client identification: {str(e)}", exc_info=True)
        return state

def client_verifier(state: State) -> State:
    """Verify identified clients against a predefined list."""
    logging.info("Verifying identified clients")
    if not state.clients:
        return state
    
    verified_clients = []
    for client in state.clients:
        if verify_client(client):
            verified_clients.append(client)
    
    # return State(
    #         verified_clients=verified_clients
    # )
    
    print (f"\n\n\n\n ***********************State in Client Verifier ***********************: {state} \n\n\n\n")

    return {"verified_clients": verified_clients}
    # return State(
    #         verified_clients=verified_clients,
    #         **{key: getattr(state, key) for key in state.__fields__ if key not in ["verified_clients"]}
    #     )
    # return State(**{**state.model_dump(), "verified_clients": verified_clients})

async def document_summarizer(state: State) -> State:
    """Summarize the document content."""
    try:
        logging.info("Summarizing document")
        result = await Runner.run(
            summarization_agent,
            state.document_content
        )
        # new_state = state.model_dump()  # Convert to dict
        # new_state["summary"] = result.final_output  # Update only required fields
        
        # return State(
        #     summary=result.final_output,
        #     # clients=state.clients,  # Preserve other fields explicitly
        #     # verified_clients=state.verified_clients,
        #     # email_details=state.email_details,
        #     # email_sent=state.email_sent,
        #     # recipient_email=state.recipient_email,
        #     # email_from_alias=state.email_from_alias
        # )
        print (f"\n\n\n\n ***********************State in Summarizer ***********************: {state} \n\n\n\n")

        return {"summary": result.final_output}
        # return State(**new_state) 
        # return State(**{**state.model_dump(), "summary": result.final_output})
    except Exception as e:
        logging.error(f"Error in document summarization: {str(e)}", exc_info=True)
        return state

async def email_drafter(state: State) -> State:
    """Draft an email based on the document summary."""
    try:
        if not state.summary and not state.verified_clients:
            logging.error("Document content is missing or verified clients are missing. Skipping Email Draft.")
            return state
        
        logging.info("Drafting email")
        result = await Runner.run(
            draft_email_agent,
            state.summary
        )
        
        print (f"\n\n\n\n ***********************State in Email Drafter ***********************: {state} \n\n\n\n")

        return {"email_details": result.final_output}
        # return State(
        #     email_details=result.final_output,
        #     **{key: getattr(state, key) for key in state.__fields__ if key not in ["email_details"]}
        # )
        # return State(**new_state) 
        # return State(**{**state.model_dump(), "email_details": result.final_output})
    except Exception as e:
        logging.error(f"Error in email drafting: {str(e)}", exc_info=True)
        return state

# async def email_sender(state: State) -> State:
#     """Send the email with the summary attached."""
#     if not state.email_details:
#         return state
    
#     try:
#         logging.info(f"Sending email to {state.recipient_email}")
#         email_input = {
#             "recipient_email": state.recipient_email,
#             "subject": state.email_details.subject,
#             "body": state.email_details.body,
#             "summary": state.summary,
#             "email_from_alias": state.email_from_alias
#         }
        
#         result = await Runner.run(
#             send_email_agent,
#             [
#                 {
#                     "role": "user",
#                     "content": f"""
#                     Please send an email to {state.recipient_email} with email from alias '{state.email_from_alias}'
#                     with the subject '{email_input['subject']}', the following body text, 
#                     and an attached summary file.

#                     Body:
#                     {email_input['body']}

#                     Summary (to be attached as 'summary.txt'):
#                     {email_input['summary']}
#                     """,
#                 }
#             ]
#         )
        
#         return State(**{**state.model_dump(), "email_sent": "successfully" in result.final_output.lower()})
#     except Exception as e:
#         logging.error(f"Error in email sending: {str(e)}", exc_info=True)
#         return state

async def email_sender_with_doc_attached(state: State) -> State:
    """Send the email with the summary attached."""
    if not state.email_details:
        return state
    
    email_sent = False  # Track if any email was successfully sent

    try:
        for client in state.verified_clients:
            assistants= get_assistants_for_client(client)
            if assistants:
                print(f"Assistants for {client}:")
                for assistant in assistants:
                    print(f"- Name: {assistant['name']}, Email: {assistant['email']}")
                    email_input = {
                        "recipient_name": assistant['name'],
                        "recipient_email": assistant['email'],
                        "subject": state.email_details.subject,
                        "body": state.email_details.body,
                        "email_from_alias": state.email_from_alias,
                        "file_path":state.document_path,
                        "file_name":state.document_name
                    }
                    logging.info(f"---------------Sending email to {email_input['recipient_name']} ---------------")

                    result = await Runner.run(
                        send_email_with_doc_attached_agent,
                        [
                            {
                                "role": "user",
                                "content": f"""
                                Please send an email to {email_input['recipient_email']} with email from alias '{state.email_from_alias}'
                                with the subject '{email_input['subject']}' and the greeting to {email_input['recipient_name']} with the following body text, 
                                and an attached the file as per {email_input['file_path']} with the file name {email_input['file_name']} .

                                Body:
                                {email_input['body']}
                                """,
                            }
                        ]
                    )
                    # Update email_sent to True if the email was sent successfully
                    if "successfully" in result.final_output.lower():
                        email_sent = True
            else:
                print(f"No assistants found for client: {client}")
                logging.info(f"No assistants found for client: {client}")
        
        # Update the state based on whether any email was sent
        return State(**{**state.model_dump(), "email_sent": email_sent})
	
	# result = await Runner.run(
        #     send_email_with_doc_attached_agent,
        #     [
        #         {
        #             "role": "user",
        #             "content": f"""
        #             Please send an email to {state.recipient_email} with email from alias '{state.email_from_alias}'
        #             with the subject '{email_input['subject']}', the following body text, 
        #             and an attached the file as per {email_input['file_path']} with the file name {email_input['file_name']} .

        #             Body:
        #             {email_input['body']}
        #             """,
        #         }
        #     ]
        # )
        
        
    except Exception as e:
        logging.error(f"Error in email sending: {str(e)}", exc_info=True)
        return state
    
def create_workflow_graph(document_path: str,file_name:str):
    """Create the workflow graph using LangGraph."""
    # Create a new graph
    workflow = StateGraph(State)
    
    # Add nodes
    # workflow.add_node("document_processor", document_processor)
    workflow.add_node("document_processor", lambda state: asyncio.run(document_processor(state, document_path,file_name)))
    workflow.add_node("client_identifier", client_identifier)
    workflow.add_node("client_verifier", client_verifier)
    workflow.add_node("document_summarizer", document_summarizer)
    workflow.add_node("email_drafter", email_drafter)
    # workflow.add_node("email_sender", email_sender)
    workflow.add_node("email_sender", email_sender_with_doc_attached)
    

    # workflow.add_edge(START,"document_processor")
    # workflow.add_edge("document_processor", "client_identifier")
    # workflow.add_edge("client_identifier", "client_verifier")
    # workflow.add_edge("client_verifier", "document_summarizer")
    # # workflow.add_edge("document_processor", "document_summarizer")
    # workflow.add_edge("document_summarizer", "email_drafter")
    # # workflow.add_edge("client_verifier", "email_sender")
    # # workflow.add_edge("email_drafter", "email_sender")
    # # workflow.add_edge("email_sender",END)
    # # workflow.add_edge("client_verifier",END)
    # workflow.add_edge("email_drafter",END)

    # workflow.add_edge("document_processor", "client_identifier")
    # workflow.add_edge("document_processor", "document_summarizer")  # Ensure summarizer gets document content
    # workflow.add_edge("client_identifier", "client_verifier")
    # workflow.add_edge("client_verifier", "email_drafter")
    # workflow.add_edge("document_summarizer", "email_drafter")
    # workflow.add_edge("email_drafter", END)
    
    # Define edges
    workflow.add_edge(START, "document_processor")
    workflow.add_edge("document_processor", "client_identifier")
    workflow.add_edge("document_processor", "document_summarizer")
    workflow.add_edge("client_identifier", "client_verifier")
    workflow.add_edge("document_summarizer", "email_drafter")
    workflow.add_edge("client_verifier", "email_sender")
    workflow.add_edge("email_drafter", "email_sender")
    workflow.add_edge("email_sender", END)

    # Set the entry point
    workflow.set_entry_point("document_processor")
    
    return workflow

def visualize_graph():
    """Generate and save a visualization of the workflow graph."""
    try:
        placeholder_path= "",
        placeholder_file_name=""
        # Create the workflow graph
        workflow = create_workflow_graph(document_path=placeholder_path,file_name=placeholder_file_name)

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
