# Document Processing & Email Workflow

A streamlined intelligent workflow application for document processing and client management using AI agents and LangGraph orchestration.

## Project Overview

This project automates the process of:
1. Extracting and analyzing content from documents (PDF/DOCX)
2. Identifying client names from both text and images
3. Verifying clients against known databases
4. Sending personalized emails with document attachments to relevant contacts

The workflow is visualized through an interactive graph that shows the processing pipeline stages.

## Setup Instructions

### Prerequisites
- Python 3.9 or higher
- OpenAI API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/publishingValidation.git
   ```

2. Set up a virtual environment:
   
   For macOS/Linux:
   ```bash
   # Create a virtual environment
   python3 -m venv venv
   
   # Activate the virtual environment
   source venv/bin/activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with:
   ```
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_BASE_URL="your_openai_api_base_url"
   SMTP_SERVER="your_smtp_server"
   SMTP_PORT="your_smtp_port"
   EMAIL_SENDER="your_email_sender"
   EMAIL_PASSWORD="your_email_password"
   ```

5. Optional: Update client data in `data.json` with your specific client information

## Running the Application

1. Ensure your virtual environment is activated:
   
   For macOS/Linux:
   ```bash
   source venv/bin/activate
   ```
2. Start the Streamlit application:
   ```bash
   streamlit run app.py
   ```

3. Access the application through your browser at http://localhost:8501

4. Upload a document (PDF or DOCX) using the sidebar uploader

5. Set your email alias in the sidebar

6. Click "Show Workflow Graph" to visualize the processing pipeline

7. Click "Process Document" to start the workflow

8. Follow the progress bar as the document is processed through each stage

## Sample Documents

The `DummyDocs` folder contains sample documents you can use to test the application:
- `AI.docx` - AI-related content with client references
- `Digital_Marketing_Trends_2025_Enhanced.docx` - Marketing document with multiple client mentions

## Key Features

- **AI-Powered Extraction**: Uses OpenAI for intelligent text and image analysis
- **Multi-Stage Processing**: Orchestrated workflow with visual progress indicators
- **Client Verification**: Matches extracted client names against your database
- **Email Automation**: Automatically sends personalized emails with attachments
- **Visual Workflow**: Interactive graph visualization of the entire process

## Technologies

- Streamlit (UI)
- LangGraph & LangChain (Workflow orchestration)
- OpenAI (Text and image analysis)
- Python-DOCX & PyPDF2 (Document parsing)
- NetworkX & PyDot (Graph visualization)