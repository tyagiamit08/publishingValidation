import os
import logging
import asyncio
from langgraph.graph import StateGraph, START, END
from src.models import State
import networkx as nx
import matplotlib.pyplot as plt
import base64
from networkx.drawing.nx_pydot import graphviz_layout

from src.nodes import (
    client_identifier,
    client_verifier,
    client_consolidator,
    extract_images_node,
    extract_client_names_node,
    document_processor,
    email_sender_with_doc_attached
)
from IPython.display import Image, display
import re
import ast

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_workflow_graph(document_path: str, file_name: str):
    """Create the workflow graph using LangGraph."""
    # Create a new graph
    workflow = StateGraph(State)

    # Define nodes
    workflow.add_node("document_processor", lambda state: asyncio.run(document_processor(state, document_path, file_name)))
    workflow.add_node("client_identifier", client_identifier)
    workflow.add_node("extract_images", extract_images_node)
    workflow.add_node("extract_clients", extract_client_names_node)
    workflow.add_node("client_consolidator", client_consolidator)
    workflow.add_node("client_verifier", client_verifier)
    workflow.add_node("email_sender", email_sender_with_doc_attached)
    
    # Define a sequential workflow instead of branching
    workflow.add_edge(START, "document_processor")
    workflow.add_edge("document_processor", "client_identifier")
    workflow.add_edge("document_processor", "extract_images")
    workflow.add_edge("extract_images", "extract_clients")
    workflow.add_edge("client_identifier", "client_consolidator")
    workflow.add_edge("extract_clients", "client_consolidator")
    workflow.add_edge("client_consolidator", "client_verifier")
    workflow.add_edge("client_verifier", "email_sender")
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

# def visualize_graph():
#     """Generate and save a visualization of the workflow graph using NetworkX + Matplotlib."""
#     try:
#         placeholder_path = ""
#         placeholder_file_name = ""

#         # Create the workflow graph
#         workflow = create_workflow_graph(document_path=placeholder_path, file_name=placeholder_file_name)

#         # Compile the workflow and generate the graph
#         graph = workflow.compile().get_graph(xray=True)

#         # Define file paths
#         output_dir = "src/images"
#         os.makedirs(output_dir, exist_ok=True)
#         graph_image_path = os.path.join(output_dir, "workflow_graph.png")

#         # Convert to NetworkX graph
#         G = nx.DiGraph()
#         for edge in graph.edges:
#             G.add_edge(edge.source, edge.target)

#         # Use Graphviz dot layout for better structure
#         pos = graphviz_layout(G, prog="dot")  # Uses hierarchical layout

#         # Draw the graph
#         # plt.figure(figsize=(5,6))
#         plt.figure(figsize=(7, 8))  # Slightly increase figure size
#         nx.draw(G, pos, 
#                 with_labels=True, 
#                 node_color="lightblue", 
#                 edge_color="gray", 
#                 node_size=2000,  # Reduce node size
#                 font_size=12,     # Ensure font fits inside
#                 font_weight="bold",
#                 arrows=True)
#         # nx.draw(G, pos, with_labels=True, node_color="lightblue", edge_color="gray", node_size=2000, font_size=10, arrows=True)
#         plt.savefig(graph_image_path)
#         plt.close()

#         return graph_image_path

#     except Exception as e:
#         print(f"Error generating workflow graph: {e}")