import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Email Configuration
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT", "465")


# Agent models
DOC_PROCESSING_MODEL = "gpt-3.5-turbo"
CLIENT_IDENTIFICATION_MODEL = "o1"
TEXT_TO_IMAGE_IDENTIFICATION_MODEL="gpt-4-turbo"

VALID_CLIENTS = ["Neste", "IBM", "IKEA", "Microsoft", "Unilever","Amazon"]