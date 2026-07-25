"""Authentication request and response schemas."""

from pydantic import BaseModel, Field

from ..models import UserPublic


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=72)
    country: str = Field(default="Malaysia", min_length=1, max_length=80)
    language: str = Field(default="English", min_length=1, max_length=80)
    preferred_categories: list[str] = Field(default_factory=list, max_length=20)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=72)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)


class ResetPasswordRequest(BaseModel):
    reset_token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=72)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic


class MessageResponse(BaseModel):
    message: str
    reset_token: str | None = None
