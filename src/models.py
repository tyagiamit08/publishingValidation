from pydantic import BaseModel, Field
from typing import List, Optional

class ClientInfo(BaseModel):
    name: str = Field(..., description="The identified client or company name.")

class ClientIdentificationResult(BaseModel):
    clients: List[ClientInfo] = Field(..., description="A list of identified clients with relevant details.")

class EmailDetail(BaseModel):
    subject: str = Field(..., description="The subject of the email.")
    body: str = Field(..., description="The body content of the email.")

class State(BaseModel):
    document_path: str
    document_content: str
    clients: Optional[ClientIdentificationResult] = None
    verified_clients: List[str] = []
    summary: str = ""
    email_details: Optional[EmailDetail] = None
    email_sent: bool = False
    recipient_email: str = ""
    email_from_alias: str = ""