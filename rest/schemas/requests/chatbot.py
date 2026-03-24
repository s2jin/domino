from pydantic import BaseModel, Field
from typing import Optional


class CreateSessionRequest(BaseModel):
    title: Optional[str] = Field(default="New Chat", description="Chat session title")


class UpdateSessionRequest(BaseModel):
    title: str = Field(..., description="New title for the chat session")


class SendMessageRequest(BaseModel):
    content: str = Field(..., description="User message content")
