import logging
import smtplib
from email.message import EmailMessage
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    trace,
    function_tool,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from src.models import EmailDetail
from config import (
    OPENAI_API_BASE, OPENAI_API_KEY, EMAIL_DRAFTING_MODEL, 
    EMAIL_SENDING_MODEL, EMAIL_SENDER, EMAIL_PASSWORD, 
    SMTP_SERVER, SMTP_PORT         
    )

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

client = AsyncOpenAI(
    base_url=OPENAI_API_BASE,
    api_key=OPENAI_API_KEY,
)

set_default_openai_client(client=client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=True)


# Email drafting instructions
EMAIL_DRAFTING_INSTRUCTION = """
You are an expert email drafting agent. Your task is to create a professional and engaging email based on the provided summary.
The email should include:
- A clear and concise subject line summarizing the purpose of the email.
- A well-structured body that includes:
    - A greeting.
    - A brief introduction or context.
    - The key points from the summary.
    - A closing statement with a call to action, if applicable.
Ensure the tone is professional and appropriate for the recipient. Don't explicitly ask to connect or meet or setup a followup discussion. 
The email should simply provide the summary and express willingness to discuss further if needed.
"""

# Email sending instructions
EMAIL_SENDING_INSTRUCTION = """
You are an email-sending expert. Your task is to send an email with the provided summary as an attachment.
Send a professional email to the recipient with the subject and body provided from the context.
The input will include:
- recipient_email: The email address of the recipient.
- subject: The subject of the email.
- body: The body of the email.
- summary: The summary content to be attached as a file.
Save the summary as a text file named 'summary.txt' and attach it to the email.
Ensure the email is sent successfully using the provided SMTP server details.
"""

# Create email drafting agent
draft_email_agent = Agent(
    name="Email Drafting Agent",
    instructions=EMAIL_DRAFTING_INSTRUCTION,
    model=EMAIL_DRAFTING_MODEL,
    output_type=EmailDetail,
)

@function_tool
def send_email_tool(recipient_email: str, subject: str, body: str, summary: str, email_from_alias: str = None) -> str:
    """Sends an email with the provided details and attaches the summary."""
    try:
        # Log the email details
        logging.info(f"Attempting to send email to: {recipient_email}")
        logging.info(f"Subject: {subject}")
        logging.info(f"Body: {body}")
        if email_from_alias:
            logging.info(f"Email From Alias: {email_from_alias}")

        # Create the email
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{email_from_alias} <{EMAIL_SENDER}>" if email_from_alias else EMAIL_SENDER
        msg["To"] = recipient_email
        msg.set_content(body)

        # Attach the summary as a text file
        msg.add_attachment(summary.encode("utf-8"), maintype="text", subtype="plain", filename="summary.txt")

        # Send the email using SMTP
        with smtplib.SMTP_SSL(SMTP_SERVER, int(SMTP_PORT)) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

        logging.info("Email sent successfully!")
        return "Email sent successfully!"
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}", exc_info=True)
        return f"Error sending email: {str(e)}"

# Create email sending agent
send_email_agent = Agent(
    name="Send Email Agent",
    instructions=EMAIL_SENDING_INSTRUCTION,
    tools=[send_email_tool],
    model=EMAIL_SENDING_MODEL,
    output_type=str,
)

async def draft_email(summary):
    """Draft an email based on the document summary."""
    try:
        with trace("Email Drafting Agent Execution"):
            email_detail_result = await Runner.run(
                draft_email_agent, summary
            )
            return email_detail_result.final_output
    except Exception as e:
        logging.error(f"Error drafting email: {str(e)}", exc_info=True)
        raise Exception(f"Email drafting failed: {str(e)}")

async def send_email(recipient_email, subject, body, summary, email_from_alias=None):
    """Send an email with the document summary attached."""
    try:
        with trace("Email Sending Agent Execution"):
            email_result = await Runner.run(
                send_email_agent,
                [
                    {
                        "role": "user",
                        "content": f"""
                        Please send an email to {recipient_email} with email from alias '{email_from_alias}'
                        with the subject '{subject}', the following body text, 
                        and an attached summary file.

                        Body:
                        {body}

                        Summary (to be attached as 'summary.txt'):
                        {summary}
                        """,
                    }
                ]
            )
            return email_result.final_output
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}", exc_info=True)
        raise Exception(f"Email sending failed: {str(e)}")

