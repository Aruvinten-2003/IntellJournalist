"""News collection, normalization, lookup, and bookmark services."""

import re
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any

import feedparser
from bson import ObjectId
from httpx import AsyncClient, HTTPError
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from ..config import settings
from ..models import Article, Bookmark
from .summarizer import Summarizer


_memory_bookmarks: dict[str, set[str]] = {}


def _demo_articles() -> list[Article]:
    now = datetime.now(UTC)
    rows = [
        {
            "_id": "regional-climate-talks",
            "title": "Regional leaders gather as trade and climate talks enter a decisive weekend",
            "excerpt": "Delegations are focusing on resilient supply chains, clean-energy investment and cross-border cooperation.",
            "content": "Regional leaders are discussing trade, supply-chain resilience and clean-energy investment. Negotiators are working toward a shared framework for practical cross-border cooperation.",
            "url": "https://www.reuters.com/world/",
            "publisher": "Reuters",
            "source_id": "reuters-world",
            "country": "world",
            "category": "world",
            "language": "en",
            "published_at": now - timedelta(minutes=12),
        },
        {
            "_id": "ai-standards",
            "title": "New open standards aim to make AI systems easier to evaluate",
            "excerpt": "Researchers and industry groups are proposing clearer benchmarks for reliability and transparency.",
            "content": "Researchers and industry groups have proposed open evaluation standards for artificial intelligence. The work focuses on comparable measures for reliability, safety and transparency.",
            "url": "https://www.technologyreview.com/",
            "publisher": "MIT Technology Review",
            "source_id": "technology-review",
            "country": "world",
            "category": "technology",
            "language": "en",
            "published_at": now - timedelta(minutes=28),
        },
        {
            "_id": "heat-resilience",
            "title": "Cities accelerate heat-resilience plans ahead of a warmer season",
            "excerpt": "Urban shade, cooling centres and improved alerts are central to new local programmes.",
            "content": "Cities are expanding shade, cooling centres and public warning systems. Local programmes focus on residents most exposed to extreme heat.",
            "url": "https://apnews.com/climate-and-environment",
            "publisher": "Associated Press",
            "source_id": "ap-climate",
            "country": "world",
            "category": "climate",
            "language": "en",
            "published_at": now - timedelta(minutes=41),
        },
        {
            "_id": "asian-markets",
            "title": "Asian markets steady as investors weigh fresh economic signals",
            "excerpt": "Technology and consumer shares led early gains while energy prices remained in focus.",
            "content": "Asian markets traded steadily as investors reviewed new economic data. Technology and consumer shares led early gains, while energy prices remained in focus.",
            "url": "https://www.bbc.com/news/business",
            "publisher": "BBC News",
            "source_id": "bbc-business",
            "country": "malaysia",
            "category": "business",
            "language": "en",
            "published_at": now - timedelta(hours=1),
        },
    ]
    articles = []
    for row in rows:
        material = f"{row['title']}|{row['url']}"
        row["content_hash"] = sha256(material.encode("utf-8")).hexdigest()
        articles.append(Article.model_validate(row))
    return articles


class NewsService:
    def __init__(
        self,
        database: AsyncDatabase | None = None,
        http_client: AsyncClient | None = None,
    ) -> None:
        self.database = database
        self.http_client = http_client
        self.summarizer = Summarizer()

    async def fetch_rss(self, feed_url: str) -> list[dict[str, Any]]:
        async with AsyncClient(timeout=15, follow_redirects=True) as client:
            response = await client.get(feed_url)
            response.raise_for_status()
        parsed = feedparser.loads(response.content)
        return [dict(entry) for entry in parsed.entries]

    async def fetch_news_api(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        if settings.news_api_key is None:
            return []
        query = dict(params)
        query["apiKey"] = settings.news_api_key.get_secret_value()
        client = self.http_client
        try:
            if client is not None:
                response = await client.get("https://newsapi.org/v2/top-headlines", params=query)
            else:
                async with AsyncClient(timeout=15) as temporary_client:
                    response = await temporary_client.get(
                        "https://newsapi.org/v2/top-headlines",
                        params=query,
                    )
            response.raise_for_status()
        except HTTPError:
            return []
        return list(response.json().get("articles", []))

    def normalize_article(
        self,
        raw: dict[str, Any],
        *,
        country: str = "world",
        category: str = "world",
        language: str = "en",
    ) -> Article:
        title = self.summarizer.clean_text(raw.get("title")) or "Untitled report"
        content = self.summarizer.clean_text(
            raw.get("content") or raw.get("summary") or raw.get("description")
        )
        excerpt = self.summarizer.extractive_summary(content, 2) or title
        url = raw.get("url") or raw.get("link")
        if not url:
            raise ValueError("Article URL is required")
        source = raw.get("source") or {}
        publisher = (
            source.get("name") if isinstance(source, dict) else str(source)
        ) or raw.get("publisher") or "Unknown publisher"
        published = raw.get("publishedAt") or raw.get("published")
        try:
            published_at = datetime.fromisoformat(str(published).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            published_at = datetime.now(UTC)
        material = f"{title}|{url}"
        return Article(
            title=title,
            excerpt=excerpt,
            content=content,
            url=url,
            image_url=raw.get("urlToImage"),
            publisher=publisher,
            source_id=str(raw.get("id") or publisher).lower().replace(" ", "-"),
            country=country.lower(),
            category=category.lower(),
            language=language.lower(),
            content_hash=sha256(material.encode("utf-8")).hexdigest(),
            published_at=published_at,
        )

    async def store_articles(self, articles: list[Article]) -> int:
        if self.database is None:
            return 0
        inserted = 0
        for article in articles:
            try:
                await self.database.articles.insert_one(
                    article.model_dump(by_alias=True, mode="json", exclude_none=True)
                )
                inserted += 1
            except DuplicateKeyError:
                continue
        return inserted

    async def list_articles(
        self,
        *,
        category: str | None = None,
        country: str | None = None,
        search: str | None = None,
        limit: int = 20,
    ) -> list[Article]:
        if self.database is None:
            articles = _demo_articles()
        else:
            query: dict[str, Any] = {}
            if category and category != "all":
                query["category"] = category.lower()
            if country and country != "all":
                query["country"] = country.lower()
            if search:
                query["$or"] = [
                    {"title": {"$regex": re.escape(search), "$options": "i"}},
                    {"excerpt": {"$regex": re.escape(search), "$options": "i"}},
                ]
            cursor = self.database.articles.find(query).sort("published_at", -1).limit(limit)
            documents = await cursor.to_list(length=limit)
            articles = [Article.model_validate(document) for document in documents]
            if not articles:
                articles = _demo_articles()

        if category and category != "all":
            articles = [article for article in articles if article.category == category.lower()]
        if country and country != "all":
            articles = [article for article in articles if article.country == country.lower()]
        if search:
            needle = search.casefold()
            articles = [
                article
                for article in articles
                if needle in article.title.casefold() or needle in article.excerpt.casefold()
            ]
        return articles[:limit]

    async def get_article(self, article_id: str) -> Article | None:
        if self.database is not None:
            identifiers: list[Any] = [article_id]
            if ObjectId.is_valid(article_id):
                identifiers.append(ObjectId(article_id))
            document = await self.database.articles.find_one({"_id": {"$in": identifiers}})
            if document:
                return Article.model_validate(document)
        return next(
            (article for article in _demo_articles() if article.id == article_id),
            None,
        )

    async def save_bookmark(self, user_id: str, article_id: str) -> None:
        if not await self.get_article(article_id):
            raise LookupError("Article not found")
        if self.database is None:
            _memory_bookmarks.setdefault(user_id, set()).add(article_id)
            return
        bookmark = Bookmark(user_id=user_id, article_id=article_id)
        try:
            await self.database.bookmarks.insert_one(
                bookmark.model_dump(by_alias=True, mode="json", exclude_none=True)
            )
        except DuplicateKeyError:
            pass

    async def remove_bookmark(self, user_id: str, article_id: str) -> None:
        if self.database is None:
            _memory_bookmarks.setdefault(user_id, set()).discard(article_id)
            return
        await self.database.bookmarks.delete_one(
            {"user_id": user_id, "article_id": article_id}
        )

    async def list_bookmarks(self, user_id: str) -> list[Article]:
        if self.database is None:
            ids = _memory_bookmarks.get(user_id, set())
        else:
            rows = await self.database.bookmarks.find({"user_id": user_id}).to_list(length=200)
            ids = {str(row["article_id"]) for row in rows}
        articles = [await self.get_article(article_id) for article_id in ids]
        return [article for article in articles if article is not None]
