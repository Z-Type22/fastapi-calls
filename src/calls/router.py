from fastapi import APIRouter, Request, Depends
from src.auth.jwt_service import authorize
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.calls.service import (
    set_offer,
    get_my_calls,
    create_call,
    add_user_to_call,
    remove_user_from_call
)
from src.calls.schemas import (
    CallRead, CalleeSchema, CallCreate
)
from src.users.models import User


router = APIRouter()

@router.get("/", response_model=list[CallRead])
async def read_calls(
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db)
):
    return await get_my_calls(user, db)

@router.post("/create", response_model=CallRead)
async def create(
    data: CallCreate,
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db),
):
    return await create_call(data, user, db)

@router.post("/add_callee", response_model=CallRead)
async def add_callee(
    data: CalleeSchema,
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db),
):
    return await add_user_to_call(data, user, db)

@router.post("/remove_callee", response_model=CallRead)
async def remove_callee(
    data: CalleeSchema,
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db),
):
    return await remove_user_from_call(data, user, db)

@router.post("/offer")
async def offer(
    request: Request, 
    user: User = Depends(authorize),
    db: AsyncSession = Depends(get_db),
):
    return await set_offer(request, user, db)
