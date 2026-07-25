# Chat Route Class Diagram

```mermaid
classDiagram
    direction LR

    class ChatRouter {
        <<chat.py / APIRouter>>
        +create_conversation(payload, current_user) Conversation
        +list_conversations(current_user) Conversation[]
        +get_conversation(conversation_id, current_user) Conversation
        +send_message(conversation_id, payload, current_user) StreamingResponse
        +delete_conversation(conversation_id, current_user) MessageResponse
    }

    class AIService {
        <<service>>
        +retrieve_sources(prompt) Article[]
        +generate_answer(prompt, sources) str
        +stream_answer(prompt, sources) AsyncIterator
    }

    class NewsService {
        <<service>>
        +search_articles(query, filters) Article[]
    }

    class Conversation {
        <<model>>
    }

    class Message {
        <<model>>
    }

    class AuthRouter {
        <<dependency>>
        +get_current_user(token) User
    }

    ChatRouter --> AIService : generates responses
    ChatRouter --> NewsService : retrieves sources
    ChatRouter --> Conversation : conversation response
    ChatRouter --> Message : stores messages
    ChatRouter --> AuthRouter : protects all routes
```

## Imports for `chat.py`

```python
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..database import get_database
from ..models import Conversation, Message, MessageRole, User
from ..services.ai_service import AIService
from ..services.news_service import NewsService
from .auth import get_current_user
```

