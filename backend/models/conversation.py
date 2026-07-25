"""Conversation and message models stored in MongoDB."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


PyObjectId = Annotated[str, BeforeValidator(str)]


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(BaseModel):
    """A user's AI news conversation."""

    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId | None = Field(default=None, alias="_id")
    user_id: PyObjectId
    title: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Message(BaseModel):
    """One message within a conversation."""

    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId | None = Field(default=None, alias="_id")
    conversation_id: PyObjectId
    sender_id: PyObjectId
    role: MessageRole = MessageRole.USER
    content: str = Field(min_length=1)
    article_ids: list[PyObjectId] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
