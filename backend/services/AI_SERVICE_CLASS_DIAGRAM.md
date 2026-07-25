# AI Service Class Diagram

`ai_service.py` is currently empty. This diagram defines the proposed AI orchestration service.

```mermaid
classDiagram
    direction LR

    class AIService {
        -AsyncOpenAI client
        -Summarizer summarizer
        -string model
        +answer_question(prompt, articles) str
        +stream_answer(prompt, articles) AsyncIterator~str~
        +compare_sources(prompt, articles) str
        +suggest_follow_ups(answer) list~str~
        -build_messages(prompt, context) list~dict~
        -format_citations(articles) str
    }

    class AsyncOpenAI {
        <<external client>>
        +responses.create()
    }

    class Summarizer {
        <<service>>
        +build_context(articles) str
        +extractive_summary(text) str
    }

    class Article {
        <<model>>
        +title
        +excerpt
        +url
        +publisher
    }

    class Settings {
        <<configuration>>
        +openai_api_key
    }

    AIService --> AsyncOpenAI : calls model
    AIService --> Summarizer : prepares context
    AIService --> Article : grounds answers
    AIService --> Settings : reads credentials
```

## Imports for `ai_service.py`

```python
import logging
from collections.abc import AsyncIterator, Sequence

from openai import AsyncOpenAI

from ..config import settings
from ..models import Article
from .summarizer import Summarizer
```

These imports are already covered by the current `openai` dependency.

