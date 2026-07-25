# Proposed Models Class Diagram

The Python model files are intentionally empty. This diagram defines the proposed domain model for their manual implementation.

```mermaid
classDiagram
    direction LR

    class User {
        +ObjectId id
        +string email
        +string password_hash
        +string first_name
        +string last_name
        +string country
        +string language
        +string[] preferred_categories
        +string role
        +bool is_active
        +datetime created_at
        +datetime updated_at
    }

    class Article {
        +ObjectId id
        +string title
        +string excerpt
        +string url
        +string publisher
        +string source_id
        +string country
        +string category
        +string language
        +string content_hash
        +datetime published_at
        +datetime collected_at
    }

    class Conversation {
        +ObjectId id
        +ObjectId user_id
        +string title
        +datetime created_at
        +datetime updated_at
    }

    class Message {
        +ObjectId id
        +ObjectId conversation_id
        +string role
        +string content
        +ObjectId[] article_ids
        +datetime created_at
    }

    class Bookmark {
        +ObjectId id
        +ObjectId user_id
        +ObjectId article_id
        +datetime created_at
    }

    User "1" --> "0..*" Conversation : owns
    Conversation "1" *-- "1..*" Message : contains
    Message "0..*" --> "0..*" Article : cites
    User "1" --> "0..*" Bookmark : creates
    Article "1" --> "0..*" Bookmark : is saved in
```

## Suggested file ownership

- `user.py`: `User` and `Bookmark`
- `article.py`: `Article`
- `conversation.py`: `Conversation` and `Message`
