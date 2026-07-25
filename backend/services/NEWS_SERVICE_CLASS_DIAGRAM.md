# News Service Class Diagram

`news_service.py` is currently empty. This diagram defines the proposed news collection, normalization and persistence service.

```mermaid
classDiagram
    direction LR

    class NewsService {
        -AsyncDatabase database
        -AsyncClient http_client
        +fetch_rss(feed_url) list~Article~
        +fetch_news_api(params) list~Article~
        +normalize_article(raw_article) Article
        +store_articles(articles) int
        +find_articles(filters, skip, limit) list~Article~
        +search_articles(query, filters) list~Article~
        +get_article(article_id) Article
        +save_bookmark(user_id, article_id) Bookmark
        +remove_bookmark(user_id, article_id) bool
        +list_bookmarks(user_id) list~Article~
        -content_hash(article) str
    }

    class AsyncClient {
        <<HTTP client>>
        +get(url, params)
    }

    class FeedParser {
        <<RSS parser>>
        +parse(content)
    }

    class MongoDB {
        <<AsyncDatabase>>
        +articles
        +bookmarks
    }

    class Article {
        <<model>>
    }

    class Bookmark {
        <<model>>
    }

    NewsService --> AsyncClient : downloads feeds and APIs
    NewsService --> FeedParser : parses RSS
    NewsService --> MongoDB : reads and writes
    NewsService --> Article : normalizes results
    NewsService --> Bookmark : saves articles
```

## Imports for `news_service.py`

```python
import logging
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

import feedparser
from bson import ObjectId
from httpx import AsyncClient, HTTPError
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from ..models import Article, Bookmark
```

These imports are already covered by `feedparser`, `httpx`, and `pymongo` in `requirements.txt`.

