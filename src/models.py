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
    # Changed from "multi" to "merge" annotation for document_content
    document_content:  str = "" #Annotated[str, "merge"] = ""
    document_path: str = ""
    document_name: str = ""
    clients: List[str]=[]
    verified_clients: List[str]=[] #Annotated[List[str], "merge"] = []
    summary: str = ""
    email_details: Optional[EmailDetail] = None
    email_sent: Optional[bool] = False #Annotated[Optional[bool], "merge"] = None #bool = False
    email_from_alias: str = ""
    images: list = []
    client_names: List[str]=[] #Annotated[list, "merge"] = []
    document_bytes: bytes = b""
    final_clients: List[str]=[]