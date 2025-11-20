from pydantic import BaseModel
from typing import Literal, List, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    ts: Optional[datetime] = None


class ChatRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []


class Source(BaseModel):
    id: str | None = None
    type: str | None = None
    metadata: dict = {}


class ChatResponse(BaseModel):
    answer: str


class HealthResponse(BaseModel):
    status: str
    vectorstore_loaded: bool = False
    ollama_available: bool = False


class ChatCreateRequest(BaseModel):
    user_id: str
    first_message: Optional[str] = None


class ChatSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ChatDetail(BaseModel):
    id: str
    user_id: str
    title: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime


class ChatMessageAddRequest(BaseModel):
    user_id: str
    question: str
