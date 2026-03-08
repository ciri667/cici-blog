import datetime

from pydantic import BaseModel, Field


# --- RSS Sources ---

class RssSourceCreate(BaseModel):
    name: str = Field(..., max_length=200)
    feed_url: str = Field(..., max_length=1000)
    category: str | None = Field(None, max_length=100)
    is_active: bool = True


class RssSourceUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    feed_url: str | None = Field(None, max_length=1000)
    category: str | None = Field(None, max_length=100)
    is_active: bool | None = None


class RssSourceResponse(BaseModel):
    id: int
    name: str
    feed_url: str
    category: str | None
    is_active: bool
    last_fetched_at: datetime.datetime | None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# --- News Articles ---

class NewsArticleResponse(BaseModel):
    id: int
    title: str
    slug: str
    original_url: str
    original_title: str
    source_name: str | None
    summary: str | None
    ai_commentary: str | None
    tags: list[str] | None
    category: str | None
    status: str
    cover_image_url: str | None
    published_at: datetime.datetime | None
    fetched_at: datetime.datetime
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class NewsListItem(BaseModel):
    id: int
    title: str
    slug: str
    source_name: str | None
    summary: str | None
    tags: list[str] | None
    category: str | None
    status: str
    published_at: datetime.datetime | None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class NewsListResponse(BaseModel):
    items: list[NewsListItem]
    total: int
    page: int
    page_size: int


class NewsStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|published)$")


# --- Agent Runs ---

class AgentRunResponse(BaseModel):
    id: int
    started_at: datetime.datetime
    finished_at: datetime.datetime | None
    status: str
    articles_found: int
    articles_created: int
    error_log: str | None

    model_config = {"from_attributes": True}


class AgentStatusResponse(BaseModel):
    recent_runs: list[AgentRunResponse]
    next_run_time: str | None
