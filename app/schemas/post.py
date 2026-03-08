import datetime

from pydantic import BaseModel, Field


class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., min_length=1)
    excerpt: str | None = Field(None, max_length=500)
    cover_image_url: str | None = Field(None, max_length=500)
    tags: list[str] | None = None
    category: str | None = Field(None, max_length=100)
    status: str = Field("draft", pattern="^(draft|published)$")


class PostUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    content: str | None = Field(None, min_length=1)
    excerpt: str | None = Field(None, max_length=500)
    cover_image_url: str | None = Field(None, max_length=500)
    tags: list[str] | None = None
    category: str | None = Field(None, max_length=100)
    status: str | None = Field(None, pattern="^(draft|published)$")


class PostResponse(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    excerpt: str | None
    cover_image_url: str | None
    tags: list[str] | None
    category: str | None
    status: str
    author_id: int | None
    published_at: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class PostListItem(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: str | None
    cover_image_url: str | None
    tags: list[str] | None
    category: str | None
    status: str
    published_at: datetime.datetime | None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class PostListResponse(BaseModel):
    items: list[PostListItem]
    total: int
    page: int
    page_size: int
