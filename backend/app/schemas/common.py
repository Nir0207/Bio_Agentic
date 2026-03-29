from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3)
    high_stakes: bool = False


class StreamRequest(BaseModel):
    query: str = Field(..., min_length=3)
    high_stakes: bool = False
