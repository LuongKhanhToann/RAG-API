from pydantic import BaseModel


class MessageCommon(BaseModel):
    detail: str
