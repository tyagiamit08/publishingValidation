from pydantic import BaseModel, Field
from typing import List, Optional
from typing import Annotated

class ClientInfo(BaseModel):
    name: str

class ClientIdentificationResult(BaseModel):
    clients: List[ClientInfo]

class State(BaseModel):
    document_content:  str = ""
    document_path: str = ""
    document_name: str = ""
    clients_identified: List[str]=[]
    verified_clients: List[str]=[]
    email_sent: Optional[bool] = False
    email_from_alias: str = ""
    images: list = []
    clients_from_images: List[str]=[]
    document_bytes: bytes = b""
    final_clients: List[str]=[]