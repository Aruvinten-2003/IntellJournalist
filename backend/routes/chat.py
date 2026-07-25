"""AI news chat and persisted conversation routes."""

import re
from datetime import UTC, datetime
from typing import Annotated, Any

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase

from ..database import get_optional_database
from ..models import Article, Conversation, Message, MessageRole, User
from ..schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationResponse,
    SourceReference,
)
from ..services import AIService, NewsService
from .auth import get_current_user, get_optional_current_user


router = APIRouter()


def _require_database() -> AsyncDatabase:
    database = get_optional_database()
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is unavailable",
        )
    return database


def _mongo_id(value: str) -> Any:
    return ObjectId(value) if ObjectId.is_valid(value) else value


def _conversation_response(conversation: Conversation) -> ConversationResponse:
    return ConversationResponse(
        id=str(conversation.id),
        user_id=str(conversation.user_id),
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def _rank_articles(question: str, articles: list[Article]) -> list[Article]:
    stop_words = {
        "about",
        "could",
        "leading",
        "latest",
        "news",
        "please",
        "report",
        "story",
        "summarise",
        "summarize",
        "what",
    }
    terms = {
        word
        for word in re.findall(r"[a-z0-9]+", question.casefold())
        if len(word) > 3 and word not in stop_words
    }
    if not terms:
        return articles

    scored = []
    for article in articles:
        material = (
            f"{article.title} {article.excerpt} {article.category} {article.country}"
        ).casefold()
        score = sum(1 for term in terms if term in material)
        if score:
            scored.append((score, article.published_at, article))
    if not scored:
        return articles
    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return [row[2] for row in scored[:6]]


async def _create_conversation(
    database: AsyncDatabase,
    user: User,
    title: str,
) -> Conversation:
    conversation = Conversation(user_id=str(user.id), title=title)
    document = conversation.model_dump(by_alias=True, mode="json", exclude_none=True)
    result = await database.conversations.insert_one(document)
    conversation.id = str(result.inserted_id)
    return conversation


async def _find_conversation(
    database: AsyncDatabase,
    conversation_id: str,
    user: User,
) -> Conversation:
    document = await database.conversations.find_one(
        {"_id": _mongo_id(conversation_id), "user_id": str(user.id)}
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return Conversation.model_validate(document)


@router.post("/ask", response_model=ChatResponse)
async def ask_news(
    payload: ChatRequest,
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ChatResponse:
    database = get_optional_database()
    news_service = NewsService(database)
    scope = payload.scope.strip().lower()
    category = scope if scope in {"technology", "business", "climate", "world"} else None
    country = "malaysia" if scope == "malaysia" else None
    question_text = payload.question.casefold()
    if category is None:
        if "technology" in question_text or re.search(r"\bai\b", question_text):
            category = "technology"
        elif "business" in question_text or "market" in question_text:
            category = "business"
        elif "climate" in question_text or "environment" in question_text:
            category = "climate"
    if country is None and "malaysia" in question_text:
        country = "malaysia"
    articles = await news_service.list_articles(
        category=category,
        country=country,
        limit=6,
    )
    articles = _rank_articles(payload.question, articles)

    ai_service = AIService()
    answer = await ai_service.answer_question(payload.question.strip(), articles)
    conversation_id = payload.conversation_id

    if current_user is not None and database is not None:
        if conversation_id:
            conversation = await _find_conversation(
                database,
                conversation_id,
                current_user,
            )
        else:
            conversation = await _create_conversation(
                database,
                current_user,
                payload.question.strip()[:80],
            )
            conversation_id = str(conversation.id)

        user_message = Message(
            conversation_id=str(conversation.id),
            sender_id=str(current_user.id),
            role=MessageRole.USER,
            content=payload.question.strip(),
            article_ids=[str(article.id) for article in articles],
        )
        assistant_message = Message(
            conversation_id=str(conversation.id),
            sender_id="assistant",
            role=MessageRole.ASSISTANT,
            content=answer,
            article_ids=[str(article.id) for article in articles],
        )
        await database.messages.insert_many(
            [
                user_message.model_dump(by_alias=True, mode="json", exclude_none=True),
                assistant_message.model_dump(by_alias=True, mode="json", exclude_none=True),
            ]
        )
        await database.conversations.update_one(
            {"_id": _mongo_id(str(conversation.id))},
            {"$set": {"updated_at": datetime.now(UTC)}},
        )

    sources = [
        SourceReference(**ai_service.format_citation(article, index))
        for index, article in enumerate(articles, start=1)
    ]
    return ChatResponse(
        answer=answer,
        sources=sources,
        suggestions=ai_service.suggest_follow_ups(answer),
        conversation_id=conversation_id,
        used_openai=ai_service.client is not None,
    )


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    payload: ConversationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    database: Annotated[AsyncDatabase, Depends(_require_database)],
) -> ConversationResponse:
    conversation = await _create_conversation(database, current_user, payload.title.strip())
    return _conversation_response(conversation)


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    database: Annotated[AsyncDatabase, Depends(_require_database)],
) -> list[ConversationResponse]:
    cursor = database.conversations.find({"user_id": str(current_user.id)}).sort(
        "updated_at",
        -1,
    )
    documents = await cursor.to_list(length=100)
    return [
        _conversation_response(Conversation.model_validate(document))
        for document in documents
    ]


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
)
async def get_conversation(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    database: Annotated[AsyncDatabase, Depends(_require_database)],
) -> ConversationResponse:
    conversation = await _find_conversation(database, conversation_id, current_user)
    return _conversation_response(conversation)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    database: Annotated[AsyncDatabase, Depends(_require_database)],
) -> None:
    conversation = await _find_conversation(database, conversation_id, current_user)
    await database.messages.delete_many({"conversation_id": str(conversation.id)})
    await database.conversations.delete_one({"_id": _mongo_id(str(conversation.id))})


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatResponse,
)
async def send_message(
    conversation_id: str,
    payload: ChatMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    database: Annotated[AsyncDatabase, Depends(_require_database)],
) -> ChatResponse:
    await _find_conversation(database, conversation_id, current_user)
    return await ask_news(
        ChatRequest(
            question=payload.content,
            conversation_id=conversation_id,
        ),
        current_user,
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[ChatMessageResponse],
)
async def list_messages(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    database: Annotated[AsyncDatabase, Depends(_require_database)],
) -> list[ChatMessageResponse]:
    await _find_conversation(database, conversation_id, current_user)
    rows = await database.messages.find(
        {"conversation_id": conversation_id}
    ).sort("created_at", 1).to_list(length=500)
    return [
        ChatMessageResponse(
            id=str(row["_id"]),
            conversation_id=str(row["conversation_id"]),
            role=str(row["role"]),
            content=str(row["content"]),
            article_ids=[str(value) for value in row.get("article_ids", [])],
            created_at=row["created_at"],
        )
        for row in rows
    ]
