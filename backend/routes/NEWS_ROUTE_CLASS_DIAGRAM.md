# News Route Class Diagram

```mermaid
classDiagram
    direction LR

    class NewsRouter {
        <<news.py / APIRouter>>
        +list_articles(country, category, date, language) ArticlePage
        +get_article(article_id) Article
        +search_articles(query, filters) ArticlePage
        +list_categories() string[]
        +list_countries() string[]
        +bookmark_article(article_id, current_user) Bookmark
        +remove_bookmark(article_id, current_user) MessageResponse
        +list_bookmarks(current_user) ArticlePage
    }

    class NewsService {
        <<service>>
        +find_articles(filters) Article[]
        +search_articles(query, filters) Article[]
        +get_article(article_id) Article
        +save_bookmark(user_id, article_id) Bookmark
        +remove_bookmark(user_id, article_id) bool
    }

    class Article {
        <<model>>
    }

    class Bookmark {
        <<model>>
    }

    class AuthRouter {
        <<dependency>>
        +get_current_user(token) User
    }

    NewsRouter --> NewsService : delegates news operations
    NewsRouter --> Article : response model
    NewsRouter --> Bookmark : bookmark response
    NewsRouter --> AuthRouter : protects user routes
```

## Imports for `news.py`

```python
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..database import get_database
from ..models import Article, Bookmark, User
from ..services.news_service import NewsService
from .auth import get_current_user
```

