from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    message: str
    user_id: int
    role: str


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    avatar_url: str | None
    role: str

    model_config = {"from_attributes": True}
