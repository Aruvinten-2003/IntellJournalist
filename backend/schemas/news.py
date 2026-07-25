"""News and bookmark response schemas."""

from datetime import datetime

from pydantic import BaseModel

from ..models import Article


class ArticleResponse(BaseModel):
    id: str
    title: str
    excerpt: str
    content: str
    url: str
    image_url: str | None
    publisher: str
    country: str
    category: str
    language: str
    published_at: datetime

    @classmethod
    def from_article(cls, article: Article) -> "ArticleResponse":
        return cls(
            id=str(article.id),
            title=article.title,
            excerpt=article.excerpt,
            content=article.content,
            url=str(article.url),
            image_url=str(article.image_url) if article.image_url else None,
            publisher=article.publisher,
            country=article.country,
            category=article.category,
            language=article.language,
            published_at=article.published_at,
        )


class BookmarkResponse(BaseModel):
    message: str
    article_id: str
    bookmarked: bool
