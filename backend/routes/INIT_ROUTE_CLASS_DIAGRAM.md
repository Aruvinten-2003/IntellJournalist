# Routes Package Initializer Diagram

```mermaid
classDiagram
    direction LR

    class routes___init__ {
        <<package initializer>>
        +auth_router
        +news_router
        +chat_router
    }

    class auth_py {
        <<module>>
        +router
    }

    class news_py {
        <<module>>
        +router
    }

    class chat_py {
        <<module>>
        +router
    }

    routes___init__ ..> auth_py : imports and exports
    routes___init__ ..> news_py : imports and exports
    routes___init__ ..> chat_py : imports and exports
```

## Imports for `routes/__init__.py`

```python
from .auth import router as auth_router
from .chat import router as chat_router
from .news import router as news_router

__all__ = ["auth_router", "chat_router", "news_router"]
```
