# Summarizer Class Diagram

`summarizer.py` is currently empty. This diagram defines a deterministic text-cleaning and extractive-summary service used before AI generation.

```mermaid
classDiagram
    direction LR

    class Summarizer {
        +clean_text(text) str
        +split_sentences(text) list~str~
        +extractive_summary(text, sentence_limit) str
        +summarize_articles(articles, sentence_limit) str
        +build_context(articles, character_limit) str
        +truncate(text, character_limit) str
    }

    class Article {
        <<model>>
        +title
        +excerpt
        +publisher
        +published_at
        +url
    }

    class AIService {
        <<consumer>>
        +answer_question(prompt, articles) str
    }

    Summarizer --> Article : reads article text
    AIService --> Summarizer : requests grounded context
```

## Imports for `summarizer.py`

```python
import re
from collections.abc import Sequence
from html import unescape

from ..models import Article
```

All required imports are from Python's standard library except the existing `Article` model.

