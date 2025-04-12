import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
import asyncio
import logging
from typing import Dict, Any, List
import time

# Import modules
from src.models import State
from src.graph import create_workflow_graph, visualize_graph

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="Document Processing Workflow",
    page_icon="📄",
    layout="wide"
)

# App title
st.title("📄 Document Processing & Email Workflow")
st.markdown("Upload a document to process, identify clients, summarize, and send emails.")

# Initialize session state
if "processing_complete" not in st.session_state:
    st.session_state.processing_complete = False
if "current_step" not in st.session_state:
    st.session_state.current_step = None
if "results" not in st.session_state:
    st.session_state.results = {}
if "graph_image" not in st.session_state:
    st.session_state.graph_image = None

# Create sidebar for file upload and configuration
with st.sidebar:
    st.header("Document Upload")
    uploaded_file = st.file_uploader("Upload a document", type=["docx", "pdf"])

    st.header("Email Configuration")
    # recipient_email = st.text_input("Recipient Email", "tyagiamit08@gmail.com")
    email_from_alias = st.text_input("Email From Alias", "AI Agent")
    
    #Generate workflow graph
    if st.button("Show Workflow Graph"):
        graph_path = visualize_graph()
        if os.path.exists(graph_path):
            st.session_state.graph_image = graph_path
            st.success("Workflow graph generated!")
            st.rerun()
    
    process_button = st.button("Process Document", type="primary", disabled=not uploaded_file)

# Create main layout with two columns
col1, col2 = st.columns([3, 1])

# Progress indicators in the right column
with col2:
    # Display graph visualization if available
    if st.session_state.graph_image:
        st.header("Workflow Graph")
        st.image(st.session_state.graph_image, use_container_width=True)
    else:
        st.header("Workflow Graph")
        st.info("Click 'Show Workflow Graph' in the sidebar to generate the workflow visualization")

# Main content area
with col1:

    # if process_button and uploaded_file:
    if process_button and uploaded_file:
        # Save uploaded file to temp directory
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_file_path = tmp_file.name
            file_name= uploaded_file.name
        
        try:
            # Debugging: Log before updating progress
            logging.info("Before updating progress to 'Document Processing'")

            # Update progress without restarting
            st.session_state.current_step = "Document Processing"

            # Continue with the workflow execution
            workflow_graph = create_workflow_graph(temp_file_path,file_name)
            logging.info("Workflow graph created successfully")
            
            # Create initial state
            initial_state = State(
                document_content="",
                clients_identified=[],
                verified_clients=[],
                email_sent=False,
                email_from_alias=email_from_alias,
                images=[],
                clients_from_images=[]
            )
            
            # Compile the graph
            graph_app = workflow_graph.compile()
            
            # Execute the workflow and track progress
            results = {}

            async def run_workflow():
                # Run the workflow asynchronously
                
                # Create a progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()  # For showing current stage
                
                # Define workflow stages
                stages = [
                    "Document Processing",
                    "Client Identification from Text",
                    "Image Extraction",
                    "Client Identification from Images",
                    "Client Consolidation",
                    "Client Verification",
                    "Email Preparation and Sending"
                ]
                total_stages = len(stages)
                
                # Mock progress updates (since we don't have real-time tracking in the workflow)
                for i, stage in enumerate(stages):
                    # Update progress bar
                    progress = int((i) / total_stages * 100)
                    progress_bar.progress(progress)
                    status_text.info(f"Stage {i+1}/{total_stages}: {stage}")
                    
                    # Wait a bit before starting the next stage (simulates processing time)
                    if i < total_stages - 1:  # Don't sleep after the last stage
                        await asyncio.sleep(3)
                
                # Actually run the workflow
                final_state = await graph_app.ainvoke(initial_state)
                
                # Complete the progress bar
                progress_bar.progress(100)
                status_text.success("Workflow completed successfully!")
                print(f"\n\n!!!!!!!!!!!!!!!!!!Workflow completed successfully. !!!!!!!!!!!!!!!!!!\n\n")
                
                st.session_state.results = {
                    "document_content": final_state["document_content"][:1000] + "..." if len(final_state["document_content"]) > 1000 else final_state["document_content"],
                    "clients_identified": final_state["clients_identified"],
                    "clients_from_images": final_state["clients_from_images"],
                    "verified_clients": final_state["verified_clients"],
                    "email_sent": final_state["email_sent"]
                }
                st.session_state.processing_complete = True
                
            asyncio.run(run_workflow())
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            logging.error("Error in workflow execution", exc_info=True)
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    # # Display results if processing is complete
    if st.session_state.processing_complete and st.session_state.results:
        results = st.session_state.results
        
        if results["email_sent"]:
            st.success("Email sent successfully!")

        with st.expander("Document Content (Preview)", expanded=False):
            st.text_area("Content", results["document_content"], height=200)
        
        with st.expander("Identified Clients Based on Text", expanded=True):
            if results["clients_identified"]:
                for i, client in enumerate(results["clients_identified"]):
                    st.write(f"- {client}")
        
        with st.expander("Identified Clients Based on Images", expanded=True):
            if results["clients_from_images"]:
                for i, client in enumerate(results["clients_from_images"]):
                    st.write(f"- {client}")

        with st.expander("Verified Clients", expanded=True):
            for client in results["verified_clients"]:
                st.write(f"- {client}")


