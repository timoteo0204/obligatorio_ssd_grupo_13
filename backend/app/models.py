from pydantic import BaseModel
from typing import Literal


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []


class Source(BaseModel):
    id: str | None = None
    type: str | None = None
    metadata: dict = {}


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source] = []


class HealthResponse(BaseModel):
    status: str
    vectorstore_loaded: bool = False
    ollama_available: bool = False
