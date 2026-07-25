"""Asynchronous MongoDB connection management and FastAPI dependency."""

import logging
from typing import Any

from pymongo import ASCENDING, DESCENDING, AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from .config import settings


logger = logging.getLogger(__name__)

_client: AsyncMongoClient | None = None
_database: AsyncDatabase | None = None


async def _create_indexes(database: AsyncDatabase) -> None:
    """Create the indexes required by the current domain models."""
    await database.users.create_index("email", unique=True, name="users_email_unique")
    await database.articles.create_index("url", unique=True, name="articles_url_unique")
    await database.articles.create_index("content_hash", name="articles_content_hash")
    await database.articles.create_index(
        [("country", ASCENDING), ("category", ASCENDING), ("published_at", DESCENDING)],
        name="articles_filters_published",
    )
    await database.conversations.create_index(
        [("user_id", ASCENDING), ("updated_at", DESCENDING)],
        name="conversations_user_updated",
    )
    await database.messages.create_index(
        [("conversation_id", ASCENDING), ("created_at", ASCENDING)],
        name="messages_conversation_created",
    )
    await database.bookmarks.create_index(
        [("user_id", ASCENDING), ("article_id", ASCENDING)],
        unique=True,
        name="bookmarks_user_article_unique",
    )


async def connect_to_database() -> AsyncDatabase:
    """Connect to MongoDB, verify the connection and create indexes."""
    global _client, _database

    if _database is not None:
        return _database

    client = AsyncMongoClient(
        settings.mongodb_url,
        appname=settings.app_name,
        serverSelectionTimeoutMS=settings.mongodb_connect_timeout_ms,
        uuidRepresentation="standard",
    )

    try:
        await client.admin.command("ping")
        database = client[settings.mongodb_database]
        await _create_indexes(database)
    except Exception:
        await client.close()
        logger.exception("Unable to connect to MongoDB")
        raise

    _client = client
    _database = database
    logger.info("Connected to MongoDB database '%s'", settings.mongodb_database)
    return database


async def close_database_connection() -> None:
    """Close the MongoDB client and clear the cached database handle."""
    global _client, _database

    if _client is not None:
        await _client.close()
    _client = None
    _database = None
    logger.info("MongoDB connection closed")


def get_database() -> AsyncDatabase:
    """Return the active database handle for use as a FastAPI dependency."""
    if _database is None:
        raise RuntimeError("MongoDB is not connected")
    return _database


def get_optional_database() -> AsyncDatabase | None:
    """Return the database handle, or ``None`` when local fallback mode is active."""
    return _database


def database_is_connected() -> bool:
    return _database is not None


async def database_health() -> dict[str, Any]:
    """Return a lightweight database health result without raising."""
    if _client is None or _database is None:
        return {"status": "disconnected", "database": settings.mongodb_database}
    try:
        await _client.admin.command("ping")
    except Exception as exc:
        return {
            "status": "unavailable",
            "database": settings.mongodb_database,
            "error": type(exc).__name__,
        }
    return {"status": "connected", "database": settings.mongodb_database}


# Compatibility aliases for common FastAPI/MongoDB naming conventions.
connect_to_mongo = connect_to_database
close_mongo_connection = close_database_connection
