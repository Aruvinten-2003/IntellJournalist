# Proposed Routes Class Diagram

The route modules are currently empty. This diagram defines the proposed FastAPI route structure and its dependencies.

```mermaid
classDiagram
    direction LR

    class AuthRouter {
        <<auth.py / APIRouter>>
        +register(user_data) UserResponse
        +login(credentials) TokenResponse
        +refresh_token(refresh_token) TokenResponse
        +logout(current_user) MessageResponse
        +forgot_password(email) MessageResponse
        +reset_password(token, password) MessageResponse
        +get_current_profile(current_user) UserResponse
    }

    class NewsRouter {
        <<news.py / APIRouter>>
        +list_articles(country, category, date, language) ArticlePage
        +get_article(article_id) ArticleResponse
        +search_articles(query, filters) ArticlePage
        +list_categories() string[]
        +list_countries() string[]
        +bookmark_article(article_id, current_user) BookmarkResponse
        +remove_bookmark(article_id, current_user) MessageResponse
        +list_bookmarks(current_user) ArticlePage
    }

    class ChatRouter {
        <<chat.py / APIRouter>>
        +create_conversation(current_user) ConversationResponse
        +list_conversations(current_user) ConversationPage
        +get_conversation(conversation_id, current_user) ConversationResponse
        +send_message(conversation_id, prompt, current_user) StreamingResponse
        +delete_conversation(conversation_id, current_user) MessageResponse
    }

    class AuthService {
        <<service>>
        +create_user()
        +authenticate_user()
        +create_tokens()
        +verify_token()
        +hash_password()
    }

    class NewsService {
        <<service>>
        +find_articles()
        +search_articles()
        +get_article()
        +save_bookmark()
        +remove_bookmark()
    }

    class AIService {
        <<service>>
        +retrieve_sources()
        +generate_answer()
        +stream_answer()
    }

    class MongoDB {
        <<database>>
        +users
        +articles
        +conversations
        +messages
        +bookmarks
    }

    AuthRouter --> AuthService : uses
    NewsRouter --> NewsService : uses
    ChatRouter --> AIService : uses
    ChatRouter --> NewsService : retrieves sources
    AuthService --> MongoDB : reads and writes
    NewsService --> MongoDB : reads and writes
    AIService --> MongoDB : stores conversations
```

## Suggested router prefixes

- `auth.py`: `/api/auth`
- `news.py`: `/api/news`
- `chat.py`: `/api/chat`
- `__init__.py`: exports `auth_router`, `news_router`, and `chat_router`
