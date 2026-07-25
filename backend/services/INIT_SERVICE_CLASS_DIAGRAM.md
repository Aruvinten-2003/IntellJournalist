# Services Package Initializer Diagram

```mermaid
classDiagram
    direction LR

    class services___init__ {
        <<package initializer>>
        +AIService
        +NewsService
        +Summarizer
    }

    class ai_service_py {
        <<module>>
        +AIService
    }

    class news_service_py {
        <<module>>
        +NewsService
    }

    class summarizer_py {
        <<module>>
        +Summarizer
    }

    services___init__ ..> ai_service_py : imports and exports
    services___init__ ..> news_service_py : imports and exports
    services___init__ ..> summarizer_py : imports and exports
```

## Imports for `services/__init__.py`

```python
from .ai_service import AIService
from .news_service import NewsService
from .summarizer import Summarizer

__all__ = ["AIService", "NewsService", "Summarizer"]
```
