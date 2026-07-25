"""Authentication routes with MongoDB persistence and a local development fallback."""

from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import uuid4

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pymongo.errors import DuplicateKeyError

from ..config import settings
from ..database import get_optional_database
from ..models import User, UserPublic
from ..schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
)


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_prefix}/auth/login",
    auto_error=False,
)

# A process-local store keeps authentication usable when MongoDB is not configured.
# It is intended for development only and is cleared whenever the server restarts.
_memory_users: dict[str, dict] = {}


def _normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Enter a valid email address",
        )
    return normalized


def _password_bytes(password: str) -> bytes:
    encoded = password.encode("utf-8")
    if len(encoded) > 72:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at most 72 UTF-8 bytes",
        )
    return encoded


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_password_bytes(password), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _create_token(subject: str, token_type: str, lifetime: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + lifetime,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def _decode_token(token: str, expected_type: str) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
        subject = payload.get("sub")
        if not subject or payload.get("type") != expected_type:
            raise JWTError("Unexpected token")
        return str(subject)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def _find_user(email: str) -> User | None:
    database = get_optional_database()
    if database is None:
        document = _memory_users.get(email)
    else:
        document = await database.users.find_one({"email": email})
    return User.model_validate(document) if document else None


async def _save_user(user: User) -> None:
    document = user.model_dump(by_alias=True, exclude_none=True)
    database = get_optional_database()
    if database is None:
        _memory_users[user.email] = document
        return
    try:
        await database.users.insert_one(document)
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this email",
        ) from exc


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = _decode_token(token, "access")
    user = await _find_user(email)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is unavailable",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_optional_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User | None:
    if not token:
        return None
    try:
        return await get_current_user(token)
    except HTTPException:
        return None


def _auth_response(user: User) -> AuthResponse:
    return AuthResponse(
        access_token=_create_token(
            user.email,
            "access",
            timedelta(minutes=settings.access_token_expire_minutes),
        ),
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserPublic.from_user(user),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest) -> AuthResponse:
    email = _normalize_email(payload.email)
    if await _find_user(email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this email",
        )

    user = User(
        _id=uuid4().hex,
        email=email,
        password_hash=_hash_password(payload.password),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        country=payload.country.strip(),
        language=payload.language.strip(),
        preferred_categories=payload.preferred_categories,
    )
    await _save_user(user)
    return _auth_response(user)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest) -> AuthResponse:
    user = await _find_user(_normalize_email(payload.email))
    if user is None or not _verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return _auth_response(user)


@router.post("/refresh", response_model=AuthResponse)
async def refresh(current_user: Annotated[User, Depends(get_current_user)]) -> AuthResponse:
    return _auth_response(current_user)


@router.post("/logout", response_model=MessageResponse)
async def logout(_current_user: Annotated[User, Depends(get_current_user)]) -> MessageResponse:
    return MessageResponse(message="Signed out successfully")


@router.get("/me", response_model=UserPublic)
async def profile(current_user: Annotated[User, Depends(get_current_user)]) -> UserPublic:
    return UserPublic.from_user(current_user)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(payload: ForgotPasswordRequest) -> MessageResponse:
    email = _normalize_email(payload.email)
    user = await _find_user(email)
    reset_token = None
    if user and settings.environment == "development":
        reset_token = _create_token(email, "password-reset", timedelta(hours=1))
    return MessageResponse(
        message="If an account exists for this email, password reset instructions are ready.",
        reset_token=reset_token,
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(payload: ResetPasswordRequest) -> MessageResponse:
    email = _decode_token(payload.reset_token, "password-reset")
    user = await _find_user(email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password_hash = _hash_password(payload.new_password)
    user.updated_at = datetime.now(UTC)
    document = user.model_dump(by_alias=True, exclude_none=True)
    database = get_optional_database()
    if database is None:
        _memory_users[email] = document
    else:
        await database.users.update_one(
            {"email": email},
            {
                "$set": {
                    "password_hash": user.password_hash,
                    "updated_at": user.updated_at,
                }
            },
        )
    return MessageResponse(message="Password reset successfully")
