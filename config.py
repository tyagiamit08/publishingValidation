import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Email Configuration
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT", "465")

VALID_CLIENTS = ["Neste", "IBM", "IKEA", "Microsoft", "Unilever"]

# Agent models
DOC_PROCESSING_MODEL = "gpt-3.5-turbo"
CLIENT_IDENTIFICATION_MODEL = "o1"
SUMMARIZATION_MODEL = "gpt-4"
EMAIL_DRAFTING_MODEL = "gpt-4.5-preview-2025-02-27"
EMAIL_SENDING_MODEL = "gpt-4"
