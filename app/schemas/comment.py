import datetime

from pydantic import BaseModel, EmailStr, Field


class CommentCreate(BaseModel):
    author_name: str | None = Field(None, max_length=100)
    author_email: str | None = None  # 可选邮箱手动校验
    content: str = Field(..., min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int | None
    author_name: str | None
    author_email: str | None
    content: str
    is_approved: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class CommentListResponse(BaseModel):
    items: list[CommentResponse]
    total: int
    page: int
    page_size: int


class CommentApproveRequest(BaseModel):
    is_approved: bool
