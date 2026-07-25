"""Public news and authenticated bookmark routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..database import get_optional_database
from ..models import User
from ..schemas.news import ArticleResponse, BookmarkResponse
from ..services import NewsService
from .auth import get_current_user


router = APIRouter()


def get_news_service() -> NewsService:
    return NewsService(get_optional_database())


@router.get("/articles", response_model=list[ArticleResponse])
async def list_articles(
    service: Annotated[NewsService, Depends(get_news_service)],
    category: str | None = Query(default=None, max_length=80),
    country: str | None = Query(default=None, max_length=80),
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[ArticleResponse]:
    articles = await service.list_articles(
        category=category,
        country=country,
        search=search,
        limit=limit,
    )
    return [ArticleResponse.from_article(article) for article in articles]


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: str,
    service: Annotated[NewsService, Depends(get_news_service)],
) -> ArticleResponse:
    article = await service.get_article(article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    return ArticleResponse.from_article(article)


@router.get("/bookmarks", response_model=list[ArticleResponse])
async def list_bookmarks(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[NewsService, Depends(get_news_service)],
) -> list[ArticleResponse]:
    articles = await service.list_bookmarks(str(current_user.id))
    return [ArticleResponse.from_article(article) for article in articles]


@router.post("/bookmarks/{article_id}", response_model=BookmarkResponse)
async def save_bookmark(
    article_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[NewsService, Depends(get_news_service)],
) -> BookmarkResponse:
    try:
        await service.save_bookmark(str(current_user.id), article_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return BookmarkResponse(
        message="Article bookmarked",
        article_id=article_id,
        bookmarked=True,
    )


@router.delete("/bookmarks/{article_id}", response_model=BookmarkResponse)
async def remove_bookmark(
    article_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[NewsService, Depends(get_news_service)],
) -> BookmarkResponse:
    await service.remove_bookmark(str(current_user.id), article_id)
    return BookmarkResponse(
        message="Bookmark removed",
        article_id=article_id,
        bookmarked=False,
    )
