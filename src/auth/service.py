from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, Depends, Response
from src.config import settings
from src.database import get_db
from src.users import models
from src.auth.schemas import UserCreate, UserLogin, TokensSchema
from src.users.schemas import UserRead
from src.auth.utils import get_password_hash, verify_password
from src.auth.jwt_service import (
    create_access_token, 
    create_refresh_token,
    blacklist_token,
    check_refresh_token
)
from sqlalchemy import select


async def create_user(user: UserCreate, db: AsyncSession):
    errors = []

    existing = await db.execute(select(models.User).where(models.User.email == user.email))
    if existing.scalar_one_or_none():
        errors.append({
            "loc": ["body", "email"],
            "msg": "Email already exists.",
            "type": "value_error",
            "input": user.email,
            "ctx": {}
        })

    existing = await db.execute(select(models.User).where(models.User.username == user.username))
    if existing.scalar_one_or_none():
        errors.append({
            "loc": ["body", "username"],
            "msg": "Username already exists.",
            "type": "value_error",
            "input": user.username,
            "ctx": {}
        })

    if errors:
        raise HTTPException(status_code=422, detail=errors)
    
    new_user = models.User(
        username=user.username,
        email=user.email,
        password=get_password_hash(user.password1),
        avatar=user.avatar,
        gender=user.gender
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserRead.model_validate(new_user)

async def authenticate_user(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.User)
        .where(
            models.User.username == credentials.username, 
            models.User.is_active == True
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=401,
            detail=[{
                "loc": ["body", "username"],
                "msg": "User not found.",
                "type": "value_error",
                "input": credentials.username,
                "ctx": {}
            }],
        )

    if not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=401,
            detail=[{
                "loc": ["body", "password"],
                "msg": "Incorrect username or password.",
                "type": "value_error",
                "input": credentials.password,
                "ctx": {}
            }],
        )

    return user

async def set_tokens(response: Response, user: UserLogin):
    access_token = create_access_token(user.username)
    refresh_token = create_refresh_token(user.username)

    response.set_cookie(
        key=settings.cookies.access_cookie_name,
        value=access_token,
        max_age=60 * 60,
        **settings.cookies.cookie_params,
    )

    response.set_cookie(
        key=settings.cookies.refresh_cookie_name,
        value=refresh_token,
        max_age=60 * 60 * 24 * 7,
        **settings.cookies.cookie_params,
    )

    return TokensSchema(
        access_token=access_token,
        refresh_token=refresh_token,
    )

async def get_access_token(
    response: Response, refresh_token: str | None
):
    payload = await check_refresh_token(refresh_token)
    new_access_token = create_access_token(payload["sub"])

    response.set_cookie(
        key=settings.cookies.access_cookie_name,
        value=new_access_token,
        max_age=60 * 15,
        **settings.cookies.cookie_params,
    )

    return {"access_token": new_access_token}

async def set_logout(
    response: Response, access_token: str | None, 
    refresh_token: str | None, db: AsyncSession,
):
    if access_token: await blacklist_token(access_token, db)

    if refresh_token: await blacklist_token(refresh_token, db)

    response.delete_cookie(settings.cookies.access_cookie_name)
    response.delete_cookie(settings.cookies.refresh_cookie_name)

    return {"detail": "Logged out."}
