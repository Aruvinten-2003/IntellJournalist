"""Article models stored in MongoDB."""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, HttpUrl


PyObjectId = Annotated[str, BeforeValidator(str)]


class Article(BaseModel):
    """A normalized news article collected from a trusted publisher."""

    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId | None = Field(default=None, alias="_id")
    title: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    content: str = ""
    url: HttpUrl
    image_url: HttpUrl | None = None
    publisher: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    country: str = Field(min_length=1)
    category: str = Field(min_length=1)
    language: str = Field(min_length=1)
    content_hash: str = Field(min_length=1)
    published_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
