"""User and bookmark models stored in MongoDB."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


PyObjectId = Annotated[str, BeforeValidator(str)]


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    """An Intell Journalist user account."""

    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId | None = Field(default=None, alias="_id")
    email: str = Field(min_length=3)
    password_hash: str = Field(min_length=8)
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    country: str = Field(min_length=1)
    language: str = Field(min_length=1)
    preferred_categories: list[str] = Field(default_factory=list)
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserPublic(BaseModel):
    """Safe user representation returned by authentication endpoints."""

    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId = Field(alias="_id")
    email: str
    first_name: str
    last_name: str
    country: str
    language: str
    preferred_categories: list[str] = Field(default_factory=list)
    role: UserRole = UserRole.USER
    created_at: datetime

    @classmethod
    def from_user(cls, user: User) -> "UserPublic":
        return cls.model_validate(
            user.model_dump(by_alias=True, exclude={"password_hash"})
        )


class Bookmark(BaseModel):
    """A user's saved article."""

    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId | None = Field(default=None, alias="_id")
    user_id: PyObjectId
    article_id: PyObjectId
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# Backward compatibility for the earlier class spelling.
BookMarker = Bookmark
