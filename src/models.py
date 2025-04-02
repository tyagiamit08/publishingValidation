from pydantic import BaseModel, Field
from typing import List, Optional
from typing import Annotated

class ClientInfo(BaseModel):
    name: str

class ClientIdentificationResult(BaseModel):
    clients: List[ClientInfo]

class EmailDetail(BaseModel):
    subject: str = Field(..., description="The subject of the email.")
    body: str = Field(..., description="The body content of the email.")

class State(BaseModel):
    # document_path: str
    document_content: Annotated[str, "multi"] = ""
    document_path: str = ""
    document_name: str = ""
    clients: List[str]=[]
    verified_clients: List[str] = []
    summary: str = ""
    email_details: Optional[EmailDetail] = None
    email_sent: bool = False
    recipient_email: str = ""
    email_from_alias: str = ""