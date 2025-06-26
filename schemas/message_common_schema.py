from pydantic import BaseModel
from typing import List, Optional

class MessageCommon(BaseModel):
    detail: str

class Response(BaseModel):
    answer: str
    contexts: List[str]
    sources: List[str]  