"""Validated request and response schemas for the public API."""

from .auth import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
)
from .chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationResponse,
    SourceReference,
)
from .news import ArticleResponse, BookmarkResponse

__all__ = [
    "ArticleResponse",
    "AuthResponse",
    "BookmarkResponse",
    "ChatRequest",
    "ChatResponse",
    "ChatMessageRequest",
    "ChatMessageResponse",
    "ConversationCreate",
    "ConversationResponse",
    "ForgotPasswordRequest",
    "LoginRequest",
    "MessageResponse",
    "RegisterRequest",
    "ResetPasswordRequest",
    "SourceReference",
]
