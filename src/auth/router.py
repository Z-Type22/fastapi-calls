from fastapi import APIRouter, Depends, Response, Cookie
from src.auth.schemas import UserCreate, UserLogin
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.auth.service import (
    create_user, 
    authenticate_user, 
    set_tokens,
    set_logout,
    get_access_token
)
from src.config import settings


router = APIRouter()

@router.post("/registration")
async def registration(user: UserCreate, db: AsyncSession = Depends(get_db)):
    return await create_user(user, db)

@router.post("/login")
async def login(
    response: Response,
    user: UserLogin = Depends(authenticate_user),
):
    return await set_tokens(response, user)

@router.post("/refresh")
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(
        default=None,
        alias=settings.cookies.refresh_cookie_name,
    ),
):
    return await get_access_token(response, refresh_token)

@router.post("/logout")
async def logout(
    response: Response,
    access_token: str | None = Cookie(
        default=None,
        alias=settings.cookies.access_cookie_name,
    ),
    refresh_token: str | None = Cookie(
        default=None,
        alias=settings.cookies.refresh_cookie_name,
    ),
    db: AsyncSession = Depends(get_db),
):
    return await set_logout(response, access_token, refresh_token, db)
