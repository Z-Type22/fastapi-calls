from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from fastapi import Cookie, HTTPException, Depends
from src.config import settings
from src.users import models
from src.auth.utils import encode_jwt, decode_jwt
from src.auth.models import TokenBlacklist
from sqlalchemy import select
import uuid
import jwt


def create_access_token(subject: str) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": subject,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=settings.auth_jwt.access_token_expire_minutes),
    }
    return encode_jwt(payload)


def create_refresh_token(subject: str) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": subject,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(days=settings.auth_jwt.refresh_token_expire_days),
    }
    return encode_jwt(payload)

async def check_refresh_token(refresh_token: str | None):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    
    try:
        payload = decode_jwt(refresh_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401, detail="Refresh token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401, detail="Invalid refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return payload

async def is_token_blacklisted(jti: str, db: AsyncSession) -> bool:
    result = await db.execute(
        select(TokenBlacklist).where(TokenBlacklist.jti == jti)
    )
    return result.scalar_one_or_none() is not None

async def authorize(
    access_token: str | None = Cookie(default=None, alias=settings.cookies.access_cookie_name),
    db: AsyncSession = Depends(get_db)
) -> models.User:
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Access token missing",
        )

    try:
        payload = decode_jwt(access_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Access token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid access token",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=401,
            detail="Invalid token type",
        )

    if await is_token_blacklisted(payload["jti"], db):
        raise HTTPException(401, "Token revoked")

    result = await db.execute(select(models.User).where(models.User.username == payload["sub"]))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    
    return user

async def blacklist_token(
    token: str,
    db: AsyncSession,
):
    payload = decode_jwt(token)

    expires_at = datetime.fromtimestamp(
        payload["exp"],
        tz=timezone.utc,
    )

    db.add(
        TokenBlacklist(
            jti=payload["jti"],
            expires_at=expires_at,
        )
    )
    await db.commit()
