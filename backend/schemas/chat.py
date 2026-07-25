"""AI news chat request and response schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2_000)
    scope: str = Field(default="all", max_length=80)
    conversation_id: str | None = None


class SourceReference(BaseModel):
    label: str
    title: str
    url: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceReference]
    suggestions: list[str]
    conversation_id: str | None = None
    used_openai: bool


class ConversationCreate(BaseModel):
    title: str = Field(default="New briefing", min_length=1, max_length=160)


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ChatMessageRequest(BaseModel):
    content: str = Field(min_length=2, max_length=2_000)
    article_ids: list[str] = Field(default_factory=list, max_length=20)


class ChatMessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    article_ids: list[str]
    created_at: datetime
