from fastapi import (
    APIRouter, 
    Depends, 
    Query, 
    UploadFile
)
from src.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.users.schemas import UserRead
from src.users.models import User
from src.users.service import (
    get_users, 
    get_search_users,
    set_avatar,
    get_connected_users
)
from src.auth.jwt_service import authorize
from uuid import UUID


router = APIRouter()

@router.get("/", response_model=list[UserRead])
async def read_users(
    user: User = Depends(authorize), 
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(5, ge=1, le=5)
):
    return await get_users(user, db, page, limit)

@router.get("/connected/{call_uuid}", response_model=list[UserRead])
async def connected_users(
    call_uuid: str,
    user: User = Depends(authorize), 
    db: AsyncSession = Depends(get_db),
):
    return await get_connected_users(call_uuid, user, db)

@router.get("/me", response_model=UserRead)
async def my_profile(user: User = Depends(authorize)):
    return user

@router.get("/search", response_model=list[UserRead])
async def search_users(
    q: str = Query(..., min_length=1, description="Поиск по username"),
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db),
):
    return await get_search_users(q, user, db)

@router.post("/upload_avatar")
async def upload_avatar(
    upload_file: UploadFile,
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db)
):
    return await set_avatar(user, upload_file, db)
